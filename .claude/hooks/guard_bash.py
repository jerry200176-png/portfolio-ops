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

    # 5. force branch delete / remote ref deletion
    if re.search(rf"\bgit\b{GAP}\bbranch\b{GAP}-[a-zA-Z]*D\b", cmd):
        deny(
            "Blocked: force branch delete. Forbidden without explicit "
            "Founder approval."
        )
    if re.search(
        rf"\bgit\b{GAP}\bpush\b{GAP}(--delete\b|:[A-Za-z0-9/_.-]+(?:\s|$))",
        cmd,
    ):
        deny(
            "Blocked: remote branch/ref deletion via push. Forbidden "
            "without explicit Founder approval."
        )


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
    check_git_patterns(cmd)
    check_deploy_patterns(cmd)
    check_credential_leak(cmd)

    if depth >= MAX_UNWRAP_DEPTH:
        return
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
