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

# Case 1: `<flag> "...text..."` — plain quoted string.
_DESC_QUOTED_RE = re.compile(
    rf"{_DESC_FLAGS}(\s*=?\s*)(['\"])((?:\\.|(?!\2).)*)\2", re.DOTALL
)

# Case 2: `<flag> "$(cat <<'EOF' ... EOF)"` — the heredoc-via-command-
# substitution shape used by this project's own commit/PR conventions.
# Requires the flag to directly precede `$(cat <<DELIM`, so a heredoc used
# for any other purpose (e.g. actually piped into a shell) is untouched.
_DESC_HEREDOC_RE = re.compile(
    rf"{_DESC_FLAGS}\s*=?\s*(['\"]?)\$\(\s*cat\s+<<-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\2[ \t]*\r?\n"
    r"(.*?\r?\n)"
    r"[ \t]*\3[ \t]*\)\1",
    re.DOTALL,
)


def _blank(s: str) -> str:
    return re.sub(r"[^\n]", " ", s)


def _strip_non_executed_text(cmd: str) -> str:
    """Blank out free-form descriptive text (commit messages, PR/issue
    bodies/titles) passed to -m/--body/--title/etc., including the
    heredoc-via-$(cat <<EOF) shape this project's own git conventions use,
    before dangerous-pattern scanning. Preserves string length/newlines so
    match spans elsewhere in `cmd` stay meaningful. Deliberately narrow —
    see module docstring on why full shell parsing is out of scope."""

    def _blank_heredoc(m: "re.Match") -> str:
        return m.group(0)[: m.start(4) - m.start(0)] + _blank(m.group(4)) + \
            m.group(0)[m.end(4) - m.start(0):]

    cmd = _DESC_HEREDOC_RE.sub(_blank_heredoc, cmd)

    def _blank_quoted(m: "re.Match") -> str:
        return m.group(0)[: m.start(3) - m.start(0)] + _blank(m.group(3)) + \
            m.group(0)[m.end(3) - m.start(0):]

    cmd = _DESC_QUOTED_RE.sub(_blank_quoted, cmd)
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


# --- Remote branch deletion (RULEBOOK B5) -----------------------------------
# The hook checks only what is visible in the command text: the branch NAME,
# and that exactly one literal branch is deleted per command. It cannot see PR
# state or ancestry; RULEBOOK B5 keeps those checks (no open PR; tip is a
# merged/closed PR head or already in the default branch) on the agent.

# Never deletable, case-insensitive, after stripping refs/heads/ or heads/.
PROTECTED_BRANCH_RE = re.compile(
    r"^(?:main|master|head|trunk|develop|gh-pages|releases?(?:[/_.-].*)?)$", re.I
)
# An unqualified name shaped like a version tag (v1, v1.2.3, 2.0, 2.0.0-rc1)
# may resolve to a tag on the remote. Spelling refs/heads/<name> opts out.
TAG_LIKE_RE = re.compile(r"^(?:v\d+(?:\.\d+)*|\d+(?:\.\d+)+)(?:[-+_.].*)?$", re.I)
# A name the hook cannot read literally: globs, expansions, substitutions.
UNSEEN_NAME_RE = re.compile(r"[*?\[\]{}$`\\]")

# `push` must be a whole word (not `~/repos/push-notifications`).
_PUSH_RE = re.compile(rf"\bgit\b{GAP}(?<![^\s'\",])push(?![^\s'\",])((?:(?!{SEP}).)*)")
# Shell words, also inside Python/JS list literals ('git','push',...).
_WORD_RE = re.compile(r"[^\s'\",()\[\]]+")
_PUSH_OPTS_WITH_ARG = {"-o", "--push-option", "--repo", "--receive-pack", "--exec"}
_API_DELETE_RE = re.compile(r"(?:-X|--method|--request)[\s'\",=]*DELETE\b", re.I)
_API_REF_RE = re.compile(r"git/refs/([^\s'\",()\[\]?#]*)")
_GRAPHQL_REF_MUTATION_RE = re.compile(r"\b(?:deleteRef|updateRefs)\b")


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


def _check_branch_name(name: str) -> None:
    if not name or UNSEEN_NAME_RE.search(name):
        deny(
            "Blocked: the branch to delete must be one literal name the hook "
            "can read (no globs, variables, command substitution or xargs). "
            "RULEBOOK B5."
        )
    qualified = name.startswith("refs/heads/")
    if qualified:
        short = name[len("refs/heads/"):]
    elif name.startswith("refs/") or name.lower().startswith("tags/"):
        deny(
            f"Blocked: '{name}' is not a branch. Tags and other refs may not "
            "be deleted (RULEBOOK B5)."
        )
    else:
        short = name[len("heads/"):] if name.startswith("heads/") else name
    if not short:
        _check_branch_name("")
    if PROTECTED_BRANCH_RE.match(short):
        deny(
            f"Blocked: '{name}' is a default, protected or release branch "
            "name. Deleting it is banned (RULEBOOK B5)."
        )
    if not qualified and TAG_LIKE_RE.match(short):
        deny(
            f"Blocked: '{name}' looks like a version tag. Tags may not be "
            "deleted; for a branch with this name, spell refs/heads/"
            f"{name} (RULEBOOK B5)."
        )


def _push_deletions(rest: str) -> list:
    """Branch names a `git push` deletes; denies bulk/force shapes outright."""
    deleting, bulk, positional, skip = False, False, [], False
    for tok in _words(rest):
        if skip:
            skip = False
            continue
        flag = tok.split("=", 1)[0]
        if flag in _PUSH_OPTS_WITH_ARG:
            skip = "=" not in tok
            continue
        if tok.startswith("-o"):  # -o<push-option>
            continue
        if flag in ("--mirror", "--prune"):
            deny(
                f"Blocked: git push {flag} can delete or overwrite many remote "
                "refs at once (RULEBOOK B1, B5)."
            )
        if flag.startswith("--force"):
            deny("Blocked: force push (RULEBOOK B1).")
        if flag == "--delete":
            deleting = True
        elif flag in ("--all", "--branches", "--tags"):
            bulk = True
        elif re.fullmatch(r"-[A-Za-z0-9]+", tok):
            if "f" in tok:
                deny("Blocked: force push (RULEBOOK B1).")
            deleting = deleting or "d" in tok
        elif not tok.startswith("-"):
            positional.append(tok)
    refs = positional[1:] if positional and positional[0][0] not in ":+" else positional
    if any(r.startswith("+") for r in refs):
        deny("Blocked: a '+<refspec>' push is a force push (RULEBOOK B1).")
    targets = refs if deleting else [r[1:] for r in refs if r.startswith(":")]
    if not deleting and not targets:
        return []
    if bulk or len(refs) != 1:
        deny(
            "Blocked: delete exactly one remote branch per command, named "
            "literally, after the RULEBOOK B5 checks."
        )
    if deleting and ":" in targets[0]:
        deny("Blocked: git push --delete takes a plain branch name (RULEBOOK B5).")
    return targets


def check_ref_deletion(cmd: str) -> None:
    """RULEBOOK B5: allow deleting one non-protected, literally named branch
    per command via `git push <remote> --delete|-d <branch>`, `git push
    <remote> :<branch>` or the REST refs API (DELETE .../git/refs/heads/<b>)."""
    targets = []
    for m in _PUSH_RE.finditer(cmd):
        targets += _push_deletions(m.group(1))
    for statement in re.split(SEP, cmd):
        if _GRAPHQL_REF_MUTATION_RE.search(statement):
            deny(
                "Blocked: GraphQL deleteRef/updateRefs take opaque IDs the hook "
                "cannot check. Use git push <remote> --delete <branch> or the "
                "REST refs API (RULEBOOK B5)."
            )
        if not _API_DELETE_RE.search(statement):
            continue
        for ref in _API_REF_RE.findall(statement):
            ref = urllib.parse.unquote(ref)
            if not ref.startswith("heads/"):
                deny(
                    f"Blocked: '{ref}' is not a branch. Tags and other refs may "
                    "not be deleted (RULEBOOK B5)."
                )
            targets.append("refs/" + ref)
    if len(targets) > 1:
        deny(
            "Blocked: delete exactly one remote branch per command, named "
            "literally, after the RULEBOOK B5 checks."
        )
    for name in targets:
        _check_branch_name(name)


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
    check_ref_deletion(scan_cmd)
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

    # Join backslash-newline line continuations so a genuinely multi-line
    # command isn't split into separate "statements" that individually
    # look safe.
    cmd = re.sub(r"\\\r?\n", " ", cmd)

    check_all(cmd)

    allow()


if __name__ == "__main__":
    main()
