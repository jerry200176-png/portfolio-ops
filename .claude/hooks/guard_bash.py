#!/usr/bin/env python3
"""PreToolUse hook for the Bash tool.

Reads the hook JSON payload on stdin, decides allow/deny for
destructive-git / production-deploy / credential-leak shaped commands, and
prints a PreToolUse decision JSON to stdout. Exits 0 either way (the JSON
decision is what blocks, not the exit code) so a malformed payload never
crashes the session.

This is a textual guardrail against ordinary mistakes and casual bypass
attempts (bash -c wrapping, git -C, chained commands, python/node
subprocess literals, etc.) — see docs/hook-threat-model.md for what it
does and does not reliably catch. It is not a sandbox.

Can be invoked standalone for testing:
  echo '{"tool_name":"Bash","tool_input":{"command":"git status"}}' | python3 guard_bash.py
Or run the regression suite:
  python3 test_guard_bash.py
"""
import json
import os
import re
import shlex
import subprocess
import sys
import urllib.parse

# Statement separators we treat as ending a "unit" a dangerous pattern must
# stay within. Deliberately does not attempt real shell parsing (quotes,
# subshells) — see docs/hook-threat-model.md.
SEP = r"[;&|\n]"

# Gap between a keyword and the next: matches any run of characters that is
# NOT a statement separator. This absorbs flags (`git -C /path push`),
# punctuation from other languages embedding the tokens (`"git","push"`
# inside a Python list literal), and plain whitespace uniformly, so we
# don't have to assume a token is immediately followed by the next one.
GAP = rf"(?:(?!{SEP}).)*?"

# Statement start: beginning of the string, right after a separator, or
# after `then` — plus tolerated no-op prefixes (env assignments, sudo,
# command, exec, time, nice, nohup) before the "real" program name. Used to
# anchor patterns built on words that are also plausible in ordinary English
# text (e.g. "deploy", "make", "release") so a commit message mentioning
# them isn't denied — only an actual invocation is.
_PREFIX = r"(?:\b(?:sudo|env(?:\s+\S+=\S*)*|command|exec|time|nice|nohup)\s+)*"
ANCHOR = rf"(?:^|{SEP}|\bthen\b)\s*{_PREFIX}"

# bash/sh/zsh/dash -c "..." / -lc '...' wrapper: extracts the quoted payload
# so it can be re-checked as its own command, since ANCHOR-based patterns
# would otherwise not see past the opening quote.
_WRAPPER_RE = re.compile(
    r"\b(?:bash|sh|zsh|dash)\s+-\w*c\w*\s+(['\"])(.*?)(?<!\\)\1", re.DOTALL
)

MAX_UNWRAP_DEPTH = 3

# Descriptive-text-only flags: their entire purpose is free-form human text
# (commit message, PR/issue body/title) — never a path, ref, or nested
# command. Scoped narrowly on purpose: this is NOT "any quoted string" or
# "any heredoc" (that would let e.g. `bash -c "$(cat <<'EOF' ... EOF)"`
# smuggle a real command past the scan) — only text captured specifically
# as the value of one of these flags is treated as non-executed.
_DESC_FLAGS = r"(?:--body|--title|--description|--message|-m|-F|--body-file)"
# For API checks `-F` is excluded: on `gh api` it is a field (`-F 'query=...'`),
# and blanking it would hide a GraphQL mutation or REST path.
_API_DESC_FLAGS = r"(?:--body|--title|--description|--message|-m|--body-file)"

# Case 1: `<flag> "...text..."` — plain quoted string.
def _desc_quoted_re(flags: str) -> "re.Pattern":
    return re.compile(rf"{flags}(\s*=?\s*)(['\"])((?:\\.|(?!\2).)*)\2", re.DOTALL)


_DESC_QUOTED_RE = _desc_quoted_re(_DESC_FLAGS)
_API_DESC_QUOTED_RE = _desc_quoted_re(_API_DESC_FLAGS)

# Case 2: `<flag> "$(cat <<'EOF' ... EOF)"` — the heredoc-via-command-
# substitution shape used by this project's own commit/PR conventions.
# Requires the flag to directly precede `$(cat <<DELIM`, so a heredoc used
# for any other purpose (e.g. actually piped into a shell) is untouched.
def _desc_heredoc_re(flags: str) -> "re.Pattern":
    return re.compile(
        rf"{flags}\s*=?\s*(['\"]?)\$\(\s*cat\s+<<-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\2[ \t]*\r?\n"
        r"(.*?\r?\n)"
        r"[ \t]*\3[ \t]*\)\1",
        re.DOTALL,
    )


_DESC_HEREDOC_RE = _desc_heredoc_re(_DESC_FLAGS)
_API_DESC_HEREDOC_RE = _desc_heredoc_re(_API_DESC_FLAGS)


def _blank(s: str) -> str:
    return re.sub(r"[^\n]", " ", s)


def _strip_non_executed_text(cmd: str, api: bool = False) -> str:
    """Blank out free-form descriptive text (commit messages, PR/issue
    bodies/titles) passed to -m/--body/--title/etc., including the
    heredoc-via-$(cat <<EOF) shape this project's own git conventions use,
    before dangerous-pattern scanning. Preserves string length/newlines so
    match spans elsewhere in `cmd` stay meaningful. Deliberately narrow —
    see module docstring on why full shell parsing is out of scope."""

    def _blank_heredoc(m: "re.Match") -> str:
        return m.group(0)[: m.start(4) - m.start(0)] + _blank(m.group(4)) + \
            m.group(0)[m.end(4) - m.start(0):]

    cmd = (_API_DESC_HEREDOC_RE if api else _DESC_HEREDOC_RE).sub(_blank_heredoc, cmd)

    def _blank_quoted(m: "re.Match") -> str:
        return m.group(0)[: m.start(3) - m.start(0)] + _blank(m.group(3)) + \
            m.group(0)[m.end(3) - m.start(0):]

    cmd = (_API_DESC_QUOTED_RE if api else _DESC_QUOTED_RE).sub(_blank_quoted, cmd)
    return cmd


def deny(reason: str) -> None:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }))
    sys.exit(0)


def allow() -> None:
    # No output = no opinion = allowed to proceed to normal permission flow.
    sys.exit(0)


def current_branch() -> str:
    # symbolic-ref works even on an unborn branch (no commits yet);
    # rev-parse --abbrev-ref HEAD can misreport "HEAD" in that case.
    for args in (["git", "symbolic-ref", "--short", "HEAD"],
                 ["git", "rev-parse", "--abbrev-ref", "HEAD"]):
        try:
            out = subprocess.run(args, capture_output=True, text=True, timeout=5)
            branch = out.stdout.strip()
            if out.returncode == 0 and branch and branch != "HEAD":
                return branch
        except Exception:
            continue
    return ""


SECRET_FILE_RE = re.compile(
    r"(\.env(?:\.[A-Za-z]+)?\b|[^;&|\s\"']*\.pem\b|\bid_rsa(?:\.\w+)?\b|"
    r"\bcredentials\.json\b|\.ssh/[A-Za-z0-9_.-]*\b)"
)


def check_git_patterns(cmd: str) -> None:
    # Deliberately NOT anchored to a statement boundary: "git" subcommand
    # shapes are specific enough (and false negatives here are worse than
    # the rare false positive of a commit message literally containing
    # e.g. "git push --force") that we search anywhere in the command.
    # See docs/hook-threat-model.md for the tradeoff.

    # 1. direct commit on main/master (flags between "git" and "commit"
    #    tolerated, e.g. `git -C /path commit`, `git --no-pager commit`).
    if re.search(rf"\bgit\b{GAP}\bcommit\b", cmd):
        branch = current_branch()
        if branch in ("main", "master"):
            deny(
                f"Blocked: direct commit on '{branch}'. Branch first — "
                "see CLAUDE.md Git rules."
            )

    # 2. force push
    force_flag = r'(--force\b|--force-with-lease\b|(?:^|[\s,"\'])-f(?:[\s,"\']|$))'
    if re.search(rf"\bgit\b{GAP}\bpush\b{GAP}{force_flag}", cmd):
        deny(
            "Blocked: force push. Forbidden without explicit Founder "
            "approval this session (CLAUDE.md)."
        )

    # 3. git reset --hard
    if re.search(rf"\bgit\b{GAP}\breset\b{GAP}--hard\b", cmd):
        deny("Blocked: git reset --hard. Forbidden — see CLAUDE.md.")

    # 4. git clean with -f/-d
    if re.search(rf"\bgit\b{GAP}\bclean\b{GAP}-[a-zA-Z]*[fd]", cmd):
        deny(
            "Blocked: git clean. Forbidden — never discard untracked work "
            "(CLAUDE.md)."
        )

    # 5. force branch delete (local; can discard unmerged commits, B6).
    #    Remote branch deletion is check_ref_deletion() (RULEBOOK B5).
    if re.search(rf"\bgit\b{GAP}\bbranch\b{GAP}-[a-zA-Z]*D\b", cmd):
        deny(
            "Blocked: force branch delete. Forbidden without explicit "
            "Founder approval."
        )


# --- Remote branch deletion and ref writes (RULEBOOK B1, B5) -----------------
# Every shell-level remote branch/tag deletion and ref write is denied, as
# strictly as before B5 2.2.0 or more. A text hook cannot parse shell, curl
# and git exactly (quoting, comments, globbing, URL normalization, option
# prefixes, config), so it never approves a deletion it parsed (review of PR
# #144). The one allowed path is `scripts/delete-merged-branch.py`, which
# verifies the branch through the GitHub API; the hook permits it only as the
# whole command in one fixed form.

# The only allowed deletion command (plus an optional --dry-run).
_DMB_ALLOWED_RE = re.compile(
    r"python3 scripts/delete-merged-branch\.py"
    r" --repo [A-Za-z0-9][A-Za-z0-9_.-]{0,99}/[A-Za-z0-9][A-Za-z0-9_.-]{0,99}"
    r" --branch (?P<branch>[A-Za-z0-9][A-Za-z0-9._/-]{0,199})(?: --dry-run)?"
)
_DELETE_HINT = (
    "Use `gh pr merge --delete-branch`, or run exactly `python3 "
    "scripts/delete-merged-branch.py --repo <owner>/<name> --branch <name>` as "
    "the whole command; it verifies the branch through the API."
)
_DENY_DELETE = (
    "Blocked: shell-level remote branch/tag deletion and ref writes are banned "
    "(RULEBOOK B1, B5). " + _DELETE_HINT
)
# Any long option that is, or is a prefix of, one of these (git accepts
# unambiguous prefixes such as --del) deletes, mirrors, prunes or forces.
_BAD_PUSH_LONG = ("--delete", "--mirror", "--prune", "--force",
                  "--force-with-lease", "--force-if-includes")
# A standalone `push` word (git push, $g push, "git" push, 'git','push').
_PUSH_WORD_RE = re.compile(r"(?<![^\s'\",;&|(`])push(?![^\s'\",;&|)`])")
_WORD_RE = re.compile(r"[^\s'\",()\[\]]+")
_HTTP_WRITE = {"DELETE", "PATCH", "POST", "PUT"}
_HTTP_READ = {"GET", "HEAD", "OPTIONS"}
_GRAPHQL_DENY_RE = re.compile(
    r"\b(?:deleteRef|updateRefs?|(?:create|update|delete)BranchProtectionRule|"
    r"(?:create|update|delete)RepositoryRuleset)\b"
)
_REF_CONFIG_RE = re.compile(
    r"\b(?:remote\.[^\s=\"']+?\.(?:push|mirror)|include(?:if\.[^\s=\"']*)?\.path|"
    r"alias\.[^\s=\"']+)\b",
    re.I,
)


def _statements(cmd: str) -> list:
    """Split at unquoted ; & | and newlines, so quoted text (a ';' inside a
    URL, a '#' argument) stays with its command. Unbalanced quotes: the whole
    command is one statement."""
    out, cur, quote, i = [], [], None, 0
    while i < len(cmd):
        c = cmd[i]
        if c == "\\" and quote != "'" and i + 1 < len(cmd):
            cur.append(cmd[i:i + 2])
            i += 2
            continue
        if quote:
            quote = None if c == quote else quote
            cur.append(c)
        elif c in "'\"":
            quote = c
            cur.append(c)
        elif c in ";&|\n":
            out.append("".join(cur))
            cur = []
        else:
            cur.append(c)
        i += 1
    if quote:
        return [cmd]
    out.append("".join(cur))
    return [s for s in out if s.strip()]


def _shell_words(stmt: str) -> list:
    try:
        return shlex.split(stmt, posix=True)
    except ValueError:  # unbalanced quotes: approximate, never fewer words
        return re.sub(r"[\\'\"]", " ", stmt).split()


def _push_rest_denied(rest: str) -> bool:
    """True if the arguments after a `push` word could delete, force, mirror
    or prune remote refs, or hide such an argument from this check."""
    if re.search(r"\$'|(?<!\$)\{|[*?\[]", rest):  # ANSI-C quoting, brace/glob expansion
        return True
    for w in _WORD_RE.findall(rest.replace("\\", "")):
        if w.startswith("--") and len(w) > 2:
            flag = w.split("=", 1)[0]
            if any(bad.startswith(flag) for bad in _BAD_PUSH_LONG):
                return True
        elif re.fullmatch(r"-[A-Za-np-z0-9]*(?:o.*)?", w) and w != "-":
            if set(w[1:].split("o", 1)[0]) & {"d", "f"}:
                return True
        elif w[0] in ":+" or re.fullmatch(r"\$\{?[@*]\}?", w):
            return True
        elif ":" in w and (w.split(":", 1)[0] == "" or re.search(r"[$`]", w.split(":", 1)[0])):
            return True
    return False


def _http_tool(words: list) -> tuple:
    """(client, index of its command word) for gh api, curl, wget or httpie."""
    for i, w in enumerate(words):
        if "://" in w:
            continue
        base = w.rsplit("/", 1)[-1]
        if base == "gh" and "api" in words[i + 1:i + 3]:
            return "gh", i
        if base in ("curl", "wget"):
            return base, i
        if base in ("http", "https", "xh", "xhs"):
            return "httpie", i
    return "", -1


# Options that take a value. curl: short letters from `curl --help all`, long
# names that matter here (curl also accepts unambiguous long prefixes). gh: pflag.
_CLI_SHORT_ARG = {"curl": set("AbcCdDeEFHKmoPQrtTuUwxXyYz"), "gh": set("XHfFqtp")}
_CLI_LONG_ARG = {
    "curl": ("request", "data", "data-raw", "data-binary", "data-urlencode", "data-ascii",
             "json", "form", "form-string", "upload-file", "header", "user", "user-agent",
             "referer", "cookie", "cookie-jar", "write-out", "output", "config", "url",
             "proxy", "oauth2-bearer", "url-query", "max-time", "connect-timeout", "retry"),
    "gh": ("method", "header", "field", "raw-field", "jq", "template", "preview", "input",
           "cache", "hostname"),
}
_CLI_LONG_FLAG = {"curl": ("get", "head", "globoff"), "gh": ("include", "paginate", "silent",
                                                                 "verbose", "slurp")}


def _parse_cli(tool: str, words: list) -> tuple:
    """Return (options, targets) for a curl or gh api call. options is a list
    of (name, value) with short clusters split per letter (`-sXPOST` is s, X=POST;
    `-d'{...}'` is d={...}); targets are the words that may name the URL/path."""
    opts, targets, i = [], [], 0
    names = _CLI_LONG_ARG[tool] + _CLI_LONG_FLAG[tool]
    while i < len(words):
        w = words[i]
        if w.startswith("--") and len(w) > 2:
            raw, eq, val = w[2:].partition("=")
            hits = [n for n in names if n == raw] or [n for n in names if n.startswith(raw)]
            # An ambiguous prefix that covers a body option counts as one (fail closed).
            name = hits[0] if len(hits) == 1 else next((h for h in hits if h in _CURL_BODY), raw)
            if not eq and name in _CLI_LONG_ARG[tool] and i + 1 < len(words):
                val, i = words[i + 1], i + 1
            opts.append((name, val if (eq or name in _CLI_LONG_ARG[tool]) else None))
            if name == "url" and val:
                targets.append(val)
        elif w.startswith("-") and len(w) > 1:
            for j, ch in enumerate(w[1:]):
                if ch in _CLI_SHORT_ARG[tool]:
                    val = w[j + 2:]
                    if not val and i + 1 < len(words):
                        val, i = words[i + 1], i + 1
                    opts.append((ch, val))
                    break
                opts.append((ch, None))
        else:
            targets.append(w)
        i += 1
    return opts, targets


_CURL_BODY = {"d", "F", "data", "data-raw", "data-binary", "data-urlencode", "data-ascii",
              "json", "form", "form-string"}


def _method_value(val: str) -> set:
    v = (val or "").upper()
    return {v} if v in _HTTP_WRITE else (set() if v in _HTTP_READ else {"?"})


def _http_methods(tool: str, words: list, opts: list) -> set:
    """Write methods the call may use; '?' marks a method the hook cannot read."""
    names = {n for n, _ in opts}
    explicit = [v for n, v in opts if n in ("X", "request", "method")]
    if tool == "curl":
        if explicit:
            return _method_value(explicit[-1])
        if names & {"T", "upload-file"}:
            return {"PUT"}
        if names & _CURL_BODY and not names & {"G", "get"}:  # -G/--get sends data as a GET
            return {"POST"}
        return set()
    if tool == "gh":
        if explicit:
            return _method_value(explicit[-1])
        return {"POST"} if names & {"f", "F", "field", "raw-field", "input"} else set()
    methods = {p.upper() for w in words for p in w.split("=") if p.upper() in _HTTP_WRITE}
    for i, w in enumerate(words):  # wget --method=X / --method X
        if re.fullmatch(r"--method(?:=.*)?", w):
            methods |= _method_value(w.partition("=")[2] or (words[i + 1] if i + 1 < len(words) else ""))
    implicit = {"wget": r"--(?:post|body)-(?:data|file)(?:=.*)?",
                "httpie": r"[^-/][^=:@/]*(?::?=|@).*"}[tool]
    if not methods and any(re.fullmatch(implicit, w) for w in words):
        methods.add("POST")
    return methods


def _graphql_body_unreadable(tool: str, opts: list) -> bool:
    """A curl/gh GraphQL body read from a file, stdin or a variable cannot be
    checked for ref mutations."""
    for name, val in opts:
        if name in ("T", "upload-file", "K", "config", "input"):
            return True
        if name in _CURL_BODY | {"f", "field", "raw-field"} and val is not None and (
                re.match(r"[@<]|[^=]*@|.*=[@<]", val) or re.search(r"[$`]", val)):
            return True
    return False


def _http_path_denied(words: list) -> bool:
    """True if a write could reach a ref, ruleset, branch protection or rename,
    or its target cannot be read: dot segments, curl globs, variables."""
    for w in words:
        prev = None
        while prev != w:  # undo nested percent-encoding
            prev, w = w, urllib.parse.unquote(w)
        if re.search(r"[$`]", w):
            return True
        if "/" not in w:
            continue
        w = re.sub(r"\{(?:owner|repo|branch)\}", "x", w)  # gh api placeholders
        if re.search(r"[\[\]{}]", w):  # curl URL globbing ranges and sets
            return True
        segs = [s.lower() for s in re.split(r"[/?#;]", w)]
        if {".", ".."} & set(segs) or {"git", "refs", "matching-refs", "rulesets"} & set(segs):
            return True
        if "branches" in segs and {"protection", "rename"} & set(segs):
            return True
    return False


# `git [global options] stash` right before a `push` word: the only exemption
# from the push check (`git stash push <pathspec>`). Global options are parsed so
# a path or value that merely ends in "stash" (`git -C /tmp/stash push`) is not it.
_GIT_GLOBAL_OPTS = (
    r"(?:\s+(?:-[Cc]\s+(?:'[^']*'|\"[^\"]*\"|\S+)|--(?:git-dir|work-tree|namespace|"
    r"exec-path|config-env|super-prefix)(?:=\S*|\s+\S+)|--(?:no-pager|paginate|bare|"
    r"no-replace-objects|literal-pathspecs|glob-pathspecs|noglob-pathspecs|icase-pathspecs|"
    r"no-optional-locks|no-advice|no-lazy-fetch)|-[pP]))*"
)
_STASH_BEFORE_PUSH_RE = re.compile(rf"(?:^|[\s;&|(`'\"])git{_GIT_GLOBAL_OPTS}\s+stash\s+$")


def check_ref_deletion(cmd: str, api_cmd: str) -> None:
    """RULEBOOK B1/B5: deny every shell-level remote ref deletion or write
    (git push, gh api, curl, wget, httpie, GraphQL); allow only the exact
    delete-merged-branch.py command."""
    if "delete-merged-branch" in cmd and re.search(r"--repo|--branch", cmd):
        m = _DMB_ALLOWED_RE.fullmatch(cmd.strip())
        branch = m.group("branch") if m else ""
        if not m or ".." in branch or "//" in branch or branch.endswith(("/", ".", ".lock")):
            deny(
                "Blocked: run exactly `python3 scripts/delete-merged-branch.py --repo "
                "<owner>/<name> --branch <name>` as the whole command: no wrapper, "
                "chaining, quoting, loop or substitution (RULEBOOK B5)."
            )
        return
    for stmt in _statements(cmd):
        if re.search(rf"\bgit\b{GAP}\b(?:send-pack|http-push)\b", stmt) or \
                re.search(r"\balias\s+[^=\s]+=.*\bpush\b", stmt):
            deny(_DENY_DELETE)
        for m in _PUSH_WORD_RE.finditer(stmt):
            if _STASH_BEFORE_PUSH_RE.search(stmt[: m.start()]):  # git stash push <pathspec>
                continue
            if _push_rest_denied(stmt[m.end():]):
                deny(_DENY_DELETE)
    for stmt in _statements(api_cmd):
        words = _shell_words(stmt)
        flat = " ".join(words)
        tool, idx = _http_tool(words)
        args = words[idx + 1:] if tool else []
        if tool in ("curl", "gh"):
            opts, targets = _parse_cli(tool, args)
        else:
            opts, targets = [], [w for w in args if not w.startswith("-")]
        if re.search(r"\bgraphql\b", flat) and (
                _GRAPHQL_DENY_RE.search(flat) or re.search(r"=@|--input\b|query=\$", flat)
                or _graphql_body_unreadable(tool, opts)):
            deny(
                "Blocked: GraphQL ref, branch-protection or ruleset mutations, and "
                "bodies the hook cannot read (from a file, stdin or a variable), are "
                "banned (RULEBOOK B1, B5)."
            )
        if tool and _http_methods(tool, args, opts) and (
                re.search(r"\$'", stmt) or _http_path_denied(targets)):
            deny(
                "Blocked: REST writes to git refs, rulesets, branch protection or "
                "renames, or to a path the hook cannot read (dot segments, globs, "
                "variables), are banned (RULEBOOK B1, B5). " + _DELETE_HINT
            )


def check_config_writes(cmd: str) -> None:
    """remote.<name>.push/.mirror, include.path and git aliases can make a
    plain `git push` delete, force or mirror refs (RULEBOOK B1, B5). Any
    statement naming them is denied unless it is exactly `git config --get
    <key>` or `git config --get-all <key>`; GIT_CONFIG* env and push mirror
    remotes are denied too."""
    for stmt in _statements(cmd):
        if re.search(rf"\bgit\b{GAP}\bremote\b{GAP}(?<![^\s'\",])--mi[a-z]*(?!=fetch)\b", stmt) \
                or re.search(r"\bGIT_CONFIG\w*=", stmt):
            deny("Blocked: push mirrors and GIT_CONFIG* overrides can rewrite pushes (RULEBOOK B1, B5).")
        words = _shell_words(stmt)
        if not (_REF_CONFIG_RE.search(stmt) or _REF_CONFIG_RE.search(" ".join(words))):
            continue
        if len(words) == 4 and words[:2] == ["git", "config"] and \
                words[2] in ("--get", "--get-all") and _REF_CONFIG_RE.fullmatch(words[3]):
            continue
        deny(
            "Blocked: setting remote.<name>.push/.mirror, include.path or a git "
            "alias can make git push delete, force or mirror refs (RULEBOOK B1, B5). "
            "Only `git config --get <key>` is allowed."
        )


def check_github_cli(cmd: str) -> None:
    """gh shapes that bypass B1/B5: --admin merge, closing a PR with
    --delete-branch, and deleting a release's tag."""
    if re.search(rf"\bgh\b{GAP}\bpr\b{GAP}\bmerge\b{GAP}(?<![^\s'\",])--admin\b", cmd):
        deny("Blocked: --admin merge bypasses required checks and review (RULEBOOK B1).")
    if re.search(
        rf"\bgh\b{GAP}\bpr\b{GAP}\bclose\b{GAP}(?<![^\s'\",])(?:--delete-branch|-[A-Za-z]*d[A-Za-z]*)\b",
        cmd,
    ):
        deny(
            "Blocked: gh pr close --delete-branch is not a B5 path. Close the PR, "
            "then use scripts/delete-merged-branch.py (RULEBOOK B5)."
        )
    if re.search(rf"\bgh\b{GAP}\brelease\b{GAP}\bdelete\b{GAP}--cleanup-tag\b", cmd):
        deny("Blocked: --cleanup-tag deletes a tag; tags may not be deleted (RULEBOOK B5).")


def check_deploy_patterns(cmd: str) -> None:
    # Anchored to statement start: these use words ("make", "deploy",
    # "release") that are common in ordinary English (commit messages, PR
    # text), so we only flag them as an actual command invocation, not
    # free text. bash -c wrapping is still caught via the unwrap pass in
    # main().
    deploy_patterns = [
        rf"{ANCHOR}vercel\b{GAP}--prod\b",
        rf"{ANCHOR}terraform\b{GAP}\bapply\b",
        rf"{ANCHOR}supabase\b{GAP}\bdb\b{GAP}\bpush\b",
        rf"{ANCHOR}prisma\b{GAP}\bmigrate\b{GAP}\bdeploy\b",
        rf"{ANCHOR}kubectl\b{GAP}\bapply\b",
        rf"{ANCHOR}gh\b{GAP}\bworkflow\b{GAP}\brun\b{GAP}deploy",
        rf"{ANCHOR}(npm|yarn|pnpm)\b{GAP}\brun\b{GAP}\bdeploy\b",
        # generic script/target invocation shapes — best-effort, not exhaustive
        rf"{ANCHOR}make\b[ \t]+(?:-\S+[ \t]+)*\b(deploy|release)\b",
        rf"{ANCHOR}\./\S*deploy\S*\.(sh|bash|py|rb|js)\b",
        rf"{ANCHOR}(sh|bash|zsh)\b\s+\S*deploy\S*\.(sh|bash)\b",
    ]
    for pat in deploy_patterns:
        if re.search(pat, cmd):
            deny(
                "Blocked: production deploy/migration command (or a script "
                "shaped like one). Requires explicit Founder approval this "
                "session (CLAUDE.md, governance/AUTONOMY_POLICY.md)."
            )


def check_credential_leak(cmd: str) -> None:
    read_verbs = r"(cat|less|more|head|tail|echo|printf)\b"
    if re.search(rf"{ANCHOR}{read_verbs}{GAP}{SECRET_FILE_RE.pattern}", cmd):
        deny(
            "Blocked: command outputs a credential-shaped file. If this is "
            "legitimate, read it deliberately and never paste the value "
            "into chat/logs (docs/security-boundaries.md)."
        )
    if re.search(rf"{ANCHOR}(curl|scp|rsync)\b{GAP}{SECRET_FILE_RE.pattern}", cmd):
        deny("Blocked: command appears to transfer a credential-shaped file externally.")

    # Symlink / indirection guard: resolve file-reading commands' path
    # arguments and check the *resolved* target, not just the literal
    # argument text — catches `cat innocuous_name` where innocuous_name is
    # a symlink to .env etc.
    for segment in re.split(SEP, cmd):
        segment = segment.strip()
        if not segment:
            continue
        tokens = segment.split()
        if not tokens or tokens[0] not in ("cat", "head", "tail", "less", "more"):
            continue
        for tok in tokens[1:]:
            if tok.startswith("-"):
                continue
            candidate = os.path.expanduser(tok)
            try:
                if not os.path.exists(candidate) and not os.path.islink(candidate):
                    continue
                resolved = os.path.realpath(candidate)
            except Exception:
                continue
            if SECRET_FILE_RE.search(resolved):
                deny(
                    "Blocked: path resolves (possibly via symlink) to a "
                    f"credential-shaped file: {os.path.basename(resolved)}. "
                    "See docs/security-boundaries.md."
                )


def check_all(cmd: str, depth: int = 0) -> None:
    scan_cmd = _strip_non_executed_text(cmd)
    check_git_patterns(scan_cmd)
    check_ref_deletion(scan_cmd, _strip_non_executed_text(cmd, api=True))
    check_config_writes(scan_cmd)
    check_github_cli(scan_cmd)
    check_deploy_patterns(scan_cmd)
    check_credential_leak(scan_cmd)

    if depth >= MAX_UNWRAP_DEPTH:
        return
    # Unwrap against the ORIGINAL (unstripped) cmd — a real bash -c payload
    # is never itself the value of a -m/--body/--title flag, so stripping
    # has no legitimate reason to touch it, and unwrapping the stripped
    # version would risk missing a wrapper whose quotes happened to look
    # like a descriptive flag's.
    for m in _WRAPPER_RE.finditer(cmd):
        inner = m.group(2)
        if inner:
            check_all(inner, depth + 1)


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        allow()
        return

    cmd = (payload.get("tool_input") or {}).get("command", "") or ""
    if not cmd:
        allow()
        return

    # Remove backslash-newline line continuations exactly as bash does (they
    # vanish, so `git pu\<newline>sh` is `git push`), so a multi-line command
    # isn't split into "statements" that individually look safe.
    cmd = re.sub(r"(?<!\\)((?:\\\\)*)\\\r?\n", r"\1", cmd)

    check_all(cmd)

    allow()


if __name__ == "__main__":
    main()
