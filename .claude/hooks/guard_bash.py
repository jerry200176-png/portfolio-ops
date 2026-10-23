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
# The hook checks only what the command text shows: that a deletion is a plain
# top-level `git push`, `gh api` or `curl` statement, deletes exactly one branch
# spelled refs/heads/<branch>, and that the name is valid and not protected.
# It cannot see PR state or ancestry; RULEBOOK B5 keeps those checks (no open
# PR; tip is a merged/closed PR head or already in the default branch) on the
# agent. Everything that writes refs another way (force, mirror, prune, config
# refspecs, REST create/update, GraphQL) or weakens the backstops B5 relies on
# (rulesets, branch protection, renames) is denied.

# Never deletable, case-insensitive (after refs/heads/).
PROTECTED_BRANCH_RE = re.compile(
    r"^(?:main|master|head|trunk|develop|gh-pages|releases?(?:[/_.-].*)?)$", re.I
)
# Characters the hook cannot read as a literal name: globs, expansions,
# substitutions, escapes and percent-encoding.
UNSEEN_NAME_RE = re.compile(r"[*?\[\]{}$`\\%'\"]")
# Statement start: optional `then`, the tolerated no-op prefixes and plain
# VAR=value assignments. A deletion must be the statement's own command, not
# an argument of xargs, parallel, find -exec, eval, bash -c, a loop or a script.
_LEAD = rf"^\s*(?:then\s+)?{_PREFIX}(?:[A-Za-z_][A-Za-z0-9_]*=[^\s;&|]*\s+)*"
_ARG = r"(?:'[^']*'|\"[^\"$`]*\"|[^\s'\"$`()]+)"
_GIT_GLOBAL = (
    rf"(?:\s+(?:-[Cc]\s+{_ARG}|--(?:git-dir|work-tree|namespace|exec-path|config-env)"
    rf"(?:=|\s+){_ARG}|--(?:no-pager|paginate|bare|no-replace-objects|literal-pathspecs|"
    r"glob-pathspecs|noglob-pathspecs|icase-pathspecs|no-optional-locks|no-advice)|-[pP]))*"
)
_TOP_PUSH_RE = re.compile(rf"{_LEAD}git{_GIT_GLOBAL}\s+(?P<push>push)(?=\s|$)")
_TOP_API_RE = re.compile(rf"{_LEAD}(?:gh\s+api|curl)(?=\s)")
# Any `push` word after `git` in the statement, also inside Python/JS list
# literals ('git','push',...). `push` must be a whole word.
_PUSH_RE = re.compile(
    rf"\bgit\b{GAP}(?<![^\s'\",])(?P<push>push)(?![^\s'\",])(?=(?P<rest>(?:(?!{SEP}).)*))"
)
# $(...) / `...` in a push's own arguments; their contents are matched separately.
_SUBST_RE = re.compile(r"\$\((?:[^()]|\([^()]*\))*\)|`[^`]*`")
# Shell words, also inside list literals.
_WORD_RE = re.compile(r"[^\s'\",()\[\]]+")

# git push long options. git accepts any unambiguous prefix (`--del`), so a
# prefix is resolved before checking; an ambiguous or unknown one is denied.
_PUSH_LONG_BASE = (
    "--all", "--branches", "--mirror", "--prune", "--dry-run", "--porcelain",
    "--delete", "--tags", "--follow-tags", "--signed", "--atomic", "--push-option",
    "--receive-pack", "--exec", "--force-with-lease", "--force-if-includes",
    "--force", "--repo", "--set-upstream", "--thin", "--quiet", "--verbose",
    "--progress", "--recurse-submodules", "--verify", "--ipv4", "--ipv6",
)
_PUSH_LONG = set(_PUSH_LONG_BASE) | {"--no-" + o[2:] for o in _PUSH_LONG_BASE}
_PUSH_LONG_WITH_ARG = {"--push-option", "--receive-pack", "--exec", "--repo"}

_HTTP_WRITE = {"DELETE", "PATCH", "POST", "PUT"}
_HTTP_READ = {"GET", "HEAD", "OPTIONS"}
_METHOD_FLAG_RE = re.compile(r"-[A-Za-z]*X(?P<val>.*)|--(?P<long>[a-z]+)(?:=(?P<lval>.*))?")
_IMPLICIT_WRITE_RE = re.compile(
    r"^(?:-[fFdT]|--(?:field|raw-field|input|data[a-z-]*|json|form[a-z-]*|upload-file)(?:=.*)?)$"
)
_GIT_API_PATH_RE = re.compile(r"(?:^|/)git/(?P<after>[^?#]*)")
_CONTROL_PATH_RE = re.compile(
    r"(?:^|/)rulesets(?:/|$)|(?:^|/)branches/.+/(?:protection|rename)(?:/|$)", re.I
)
_GRAPHQL_DENY_RE = re.compile(
    r"\b(?:deleteRef|updateRefs?|(?:create|update|delete)BranchProtectionRule|"
    r"(?:create|update|delete)RepositoryRuleset)\b"
)

_ONE_BRANCH = (
    "Blocked: delete exactly one remote branch per command, named literally "
    "as refs/heads/<branch>, after the RULEBOOK B5 checks."
)


def _words(rest: str) -> list:
    """Shell words of the rest of a statement, minus redirections/comments."""
    words, skip_next = [], False
    for tok in _WORD_RE.findall(rest):
        if tok.startswith("#"):
            break
        if skip_next:
            skip_next = False
        elif re.fullmatch(r"\d*[<>]+&?", tok):  # `>` `2>` `>>`: target follows
            skip_next = True
        elif not re.match(r"\d*[<>]", tok):  # `2>/dev/null`: target attached
            words.append(tok)
    return words


def _bad_ref_name(name: str) -> bool:
    """git check-ref-format rules for the part after refs/heads/."""
    if not name or name == "@" or "@{" in name or ".." in name or "//" in name:
        return True
    if name.startswith("/") or name.endswith(("/", ".")):
        return True
    if re.search(r"[\x00-\x20\x7f~^:?*\[\\]", name):
        return True
    return any(c.startswith(".") or c.endswith(".lock") for c in name.split("/"))


def _check_branch_name(name: str) -> None:
    if not name.startswith("refs/heads/"):
        deny(
            f"Blocked: '{name}' must be spelled refs/heads/<branch>. A bare "
            "name can resolve to a tag, and tags and other refs may not be "
            "deleted (RULEBOOK B5)."
        )
    short = name[len("refs/heads/"):]
    if UNSEEN_NAME_RE.search(short) or _bad_ref_name(short):
        deny(
            f"Blocked: '{name}' is not one literal, valid branch name (no "
            "globs, variables, substitution, escapes, percent-encoding, '.' "
            "or '..' segments). RULEBOOK B5."
        )
    if PROTECTED_BRANCH_RE.match(short):
        deny(
            f"Blocked: '{name}' is a default, protected or release branch. "
            "Deleting it is banned (RULEBOOK B5)."
        )


def _push_long_opt(flag: str, strict: bool):
    if flag in _PUSH_LONG:
        return flag
    hits = [o for o in _PUSH_LONG if o.startswith(flag)]
    if len(hits) == 1:
        return hits[0]
    if strict:
        deny(
            f"Blocked: '{flag}' is not a full git push option (abbreviated, "
            "ambiguous or unknown). Spell it out (RULEBOOK B1, B5)."
        )
    return None


def _parse_push(rest: str, strict: bool):
    """Return (deletes, refs, targets) for a `git push`'s arguments; denies
    force, mirror and prune shapes outright."""
    deleting, bulk, positional, skip, end_opts = False, False, [], False, False
    for tok in _words(_SUBST_RE.sub(" $SUBST ", rest)):
        if skip:
            skip = False
            continue
        if end_opts or not tok.startswith("-") or tok == "-":
            positional.append(tok)
            continue
        if tok == "--":
            end_opts = True
            continue
        if tok.startswith("--"):
            raw, _, value = tok.partition("=")
            flag = _push_long_opt(raw, strict)
            if flag is None:
                continue
            if flag in ("--mirror", "--prune"):
                deny(
                    f"Blocked: git push {flag} can delete or overwrite many "
                    "remote refs at once (RULEBOOK B1, B5)."
                )
            if flag.startswith("--force"):
                deny("Blocked: force push (RULEBOOK B1).")
            if flag == "--delete":
                deleting = True
            elif flag in ("--all", "--branches", "--tags"):
                bulk = True
            elif flag in _PUSH_LONG_WITH_ARG and "=" not in tok:
                skip = True
            continue
        if not re.fullmatch(r"-[A-Za-np-z0-9]*(?:o.*)?", tok):  # -o<arg> may hold anything
            continue
        cluster = tok[1:]  # short options: -d -f -u -n -q -v -4 -6 -o<arg>
        for i, ch in enumerate(cluster):
            if ch == "f":
                deny("Blocked: force push (RULEBOOK B1).")
            if ch == "d":
                deleting = True
            if ch == "o":
                skip = i == len(cluster) - 1
                break
    refs = positional[1:] if positional and positional[0][0] not in ":+" else positional
    if any(r.startswith("+") for r in refs):
        deny("Blocked: a '+<refspec>' push is a force push (RULEBOOK B1).")
    targets = refs if deleting else [r[1:] for r in refs if r.startswith(":")]
    deletes = deleting or bool(targets)
    if deletes and bulk:
        deny(_ONE_BRANCH)
    return deletes, refs, targets


def _statement_push_deletions(stmt: str) -> list:
    top = _TOP_PUSH_RE.match(stmt)
    targets = []
    for m in _PUSH_RE.finditer(stmt):
        before = re.search(r"([\w-]+)[\s'\",]*$", stmt[: m.start("push")])
        if before and before.group(1) == "stash":  # git stash push <pathspec>
            continue
        is_top = bool(top) and m.start("push") == top.start("push")
        deletes, refs, found = _parse_push(m.group("rest"), strict=is_top)
        if not deletes:
            continue
        if not is_top:
            deny(
                "Blocked: a remote branch deletion must be its own top-level "
                "`git push` statement, not run through xargs, parallel, find "
                "-exec, eval, bash -c, a loop, a script or a variable "
                "(RULEBOOK B5)."
            )
        if len(refs) != 1 or len(found) != 1:
            deny(_ONE_BRANCH)
        if ":" in found[0]:
            deny("Blocked: git push --delete takes a plain branch name (RULEBOOK B5).")
        targets += found
    return targets


def _api_methods(words: list) -> set:
    """HTTP methods a gh api / curl / wget / httpie statement may use. '?' marks
    a method the hook cannot read; implicit body flags count as POST."""
    methods, explicit = set(), False
    for i, w in enumerate(words):
        for piece in w.split("="):
            if piece.upper() in _HTTP_WRITE:
                methods.add(piece.upper())
        m = _METHOD_FLAG_RE.fullmatch(w)
        if not m:
            continue
        if m.group("long") is not None:
            if not ("request".startswith(m.group("long")) or "method".startswith(m.group("long"))) \
                    or len(m.group("long")) < 3:
                continue
            val = m.group("lval")
        else:
            val = m.group("val")
        if val is None or val == "":
            val = words[i + 1] if i + 1 < len(words) else ""
        explicit = True
        if val.upper() in _HTTP_WRITE:
            methods.add(val.upper())
        elif val.upper() not in _HTTP_READ:
            methods.add("?")
    if not explicit and not methods and any(_IMPLICIT_WRITE_RE.match(w) for w in words):
        methods.add("POST")
    return methods


def _api_pieces(stmt: str) -> list:
    """Shell words after quote removal (shlex), split at list-literal
    punctuation, URL-decoded once."""
    try:
        words = shlex.split(stmt, posix=True)
    except ValueError:  # unbalanced quotes: approximate
        words = re.sub(r"[\\'\"]", " ", stmt).split()
    return [urllib.parse.unquote(p) for w in words for p in re.split(r"[,()\[\]]+", w) if p]


_HTTP_TOOL_RE = re.compile(rf"\bgh\b{GAP}\bapi\b|\b(?:curl|wget|http|https|xh)\b")


def _statement_api_deletions(stmt: str) -> list:
    pieces = _api_pieces(stmt)
    flat = " ".join(pieces)
    if re.search(r"\bgraphql\b", flat) and (
            _GRAPHQL_DENY_RE.search(flat) or re.search(r"=@|--input\b", flat)):
        deny(
            "Blocked: GraphQL ref, branch-protection or ruleset mutations "
            "(and queries read from a file the hook cannot see) are banned; "
            "use git push <remote> --delete refs/heads/<branch> (RULEBOOK B1, B5)."
        )
    methods = _api_methods(pieces)
    if not methods:
        return []  # a read
    ref_paths = [m.group("after") for p in pieces for m in [_GIT_API_PATH_RE.search(p)]
                 if m and re.match(r"[./]*(?:matching-)?refs\b", m.group("after"), re.I)]
    if any(_CONTROL_PATH_RE.search(p) for p in pieces):
        deny(
            "Blocked: writes to rulesets, branch protection or branch renames "
            "remove the backstops RULEBOOK B5 relies on. Change them by PR."
        )
    if (methods - {"POST"}) and _HTTP_TOOL_RE.search(stmt) and any(
            re.search(r"[$`]", p) and ("/" in p or p.startswith("$")) for p in pieces):
        deny(
            "Blocked: name the API path and method literally; no variables or "
            "substitution in a REST DELETE/PATCH/PUT (RULEBOOK B5)."
        )
    if not ref_paths:
        return []
    if methods - {"DELETE"}:
        deny(
            "Blocked: REST writes to git/refs (create, update, force) are banned; "
            "push through git. Only one B5 branch DELETE is allowed (RULEBOOK B1, B5)."
        )
    if not _TOP_API_RE.match(stmt):
        deny(
            "Blocked: a REST branch deletion must be its own top-level `gh api` "
            "or `curl` statement, not run through xargs, a loop, a script or "
            "another tool (RULEBOOK B5)."
        )
    return ref_paths  # each is checked as refs/heads/<branch> by the caller


def check_ref_deletion(cmd: str, api_cmd: str) -> None:
    """RULEBOOK B5: allow deleting one valid, non-protected branch per command
    via a top-level `git push <remote> --delete|-d refs/heads/<branch>`,
    `git push <remote> :refs/heads/<branch>`, or `gh api`/`curl` DELETE
    .../git/refs/heads/<branch>. `api_cmd` keeps `-F` values (gh api fields)."""
    targets = []
    for stmt in re.split(SEP, cmd):
        targets += _statement_push_deletions(stmt)
    for stmt in re.split(SEP, api_cmd):
        targets += _statement_api_deletions(stmt)
    if len(targets) > 1:
        deny(_ONE_BRANCH)
    for name in targets:
        _check_branch_name(name)


_REMOTE_REFSPEC_KEY_RE = re.compile(r"\bremote\.[^\s=\"']+?\.(?:push|mirror)\b", re.I)


def check_config_writes(cmd: str) -> None:
    """remote.<name>.push / .mirror make a plain `git push` delete, force or
    mirror refs (RULEBOOK B1, B5). Deny setting them via -c, --config-env,
    GIT_CONFIG_* or `git config`, and `git remote add --mirror[=push]`."""
    for stmt in re.split(SEP, cmd):
        if re.search(rf"\bgit\b{GAP}\bremote\b{GAP}(?<![^\s'\",])--mi[a-z]*(?!=fetch)\b", stmt):
            deny("Blocked: a push mirror remote can delete or overwrite remote refs (RULEBOOK B1, B5).")
        if not _REMOTE_REFSPEC_KEY_RE.search(stmt):
            continue
        is_config = re.search(rf"\bgit\b{GAP}(?<![^\s'\",])config(?![^\s'\",])", stmt)
        code = re.sub(r"(?:^|\s)#.*", "", stmt)
        read_only = re.search(
            r"(?<![^\s'\",])(?:--get[a-z-]*|-l|--list)(?![^\s'\",])", code
        ) or re.search(r"\bconfig\s+(?:get|list)\b", code)
        injected = re.search(r"(?<![^\s'\",])(?:-c|--config-env)\b|GIT_CONFIG", stmt)
        if (is_config and not read_only) or injected:
            deny(
                "Blocked: setting remote.<name>.push or remote.<name>.mirror "
                "makes git push delete, force or mirror refs (RULEBOOK B1, B5)."
            )


def check_github_cli(cmd: str) -> None:
    """gh shapes that bypass B1/B5: --admin merge, closing a PR with
    --delete-branch (no visible name), and deleting a release's tag."""
    if re.search(rf"\bgh\b{GAP}\bpr\b{GAP}\bmerge\b{GAP}(?<![^\s'\",])--admin\b", cmd):
        deny("Blocked: --admin merge bypasses required checks and review (RULEBOOK B1).")
    if re.search(
        rf"\bgh\b{GAP}\bpr\b{GAP}\bclose\b{GAP}(?<![^\s'\",])(?:--delete-branch|-[A-Za-z]*d[A-Za-z]*)\b",
        cmd,
    ):
        deny(
            "Blocked: gh pr close --delete-branch deletes a branch the hook cannot "
            "name. Close the PR, then delete refs/heads/<branch> under RULEBOOK B5."
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
