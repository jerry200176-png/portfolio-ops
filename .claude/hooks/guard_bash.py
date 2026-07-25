#!/usr/bin/env python3
"""PreToolUse hook for the Bash tool.

Reads the hook JSON payload on stdin, decides allow/deny for
destructive-git / production-deploy / credential-leak shaped commands, and
prints a PreToolUse decision JSON to stdout. Exits 0 either way (the JSON
decision is what blocks, not the exit code) so a malformed payload never
crashes the session.

Can be invoked standalone for testing:
  echo '{"tool_name":"Bash","tool_input":{"command":"git status"}}' | python3 guard_bash.py
"""
import json
import re
import subprocess
import sys


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

    boundary = r"(^|[;&|]|\bthen\b)\s*"

    # 1. direct commit on main/master
    if re.search(boundary + r"git\s+commit\b", cmd):
        branch = current_branch()
        if branch in ("main", "master"):
            deny(
                f"Blocked: direct commit on '{branch}'. Branch first — "
                "see CLAUDE.md Git rules."
            )

    # 2. force push
    if re.search(r"\bgit\s+push\b", cmd) and re.search(
        r"(--force\b|--force-with-lease\b|(^|\s)-f(\s|$))", cmd
    ):
        deny(
            "Blocked: force push. Forbidden without explicit Founder "
            "approval this session (CLAUDE.md)."
        )

    # 3. git reset --hard
    if re.search(r"\bgit\s+reset\b[^;&|]*--hard\b", cmd):
        deny("Blocked: git reset --hard. Forbidden — see CLAUDE.md.")

    # 4. git clean with -f/-d
    if re.search(r"\bgit\s+clean\b[^;&|]*-[a-zA-Z]*[fd]", cmd):
        deny(
            "Blocked: git clean. Forbidden — never discard untracked work "
            "(CLAUDE.md)."
        )

    # 5. force branch delete / remote ref deletion
    if re.search(r"\bgit\s+branch\b[^;&|]*-[a-zA-Z]*D\b", cmd):
        deny(
            "Blocked: force branch delete. Forbidden without explicit "
            "Founder approval."
        )
    if re.search(r"\bgit\s+push\b[^;&|]*(--delete\b|:[A-Za-z0-9/_.-]+(\s|$))", cmd):
        deny(
            "Blocked: remote branch/ref deletion via push. Forbidden "
            "without explicit Founder approval."
        )

    # 8. production deploy / migration commands
    deploy_patterns = [
        r"\bvercel\b[^;&|]*--prod\b",
        r"\bterraform\b[^;&|]*\bapply\b",
        r"\bsupabase\b[^;&|]*\bdb\b[^;&|]*\bpush\b",
        r"\bprisma\b[^;&|]*\bmigrate\b[^;&|]*\bdeploy\b",
        r"\bkubectl\b[^;&|]*\bapply\b",
        r"\bgh\b[^;&|]*\bworkflow\b[^;&|]*\brun\b[^;&|]*deploy",
        r"\b(npm|yarn|pnpm)\b[^;&|]*\brun\b[^;&|]*\bdeploy\b",
    ]
    for pat in deploy_patterns:
        if re.search(pat, cmd):
            deny(
                "Blocked: production deploy/migration command. Requires "
                "explicit Founder approval this session (CLAUDE.md, "
                "governance/AUTONOMY_POLICY.md)."
            )

    # 9. credential-shaped file leakage (best-effort)
    secret_file = r"(\.env\b|[^;&| ]*\.pem\b|\bid_rsa\b|\bcredentials\.json\b)"
    if re.search(r"\b(cat|less|more|head|tail|echo|printf)\b[^;&|]*" + secret_file, cmd):
        deny(
            "Blocked: command outputs a credential-shaped file. If this is "
            "legitimate, read it deliberately and never paste the value "
            "into chat/logs (docs/security-boundaries.md)."
        )
    if re.search(r"\b(curl|scp|rsync)\b[^;&|]*" + secret_file, cmd):
        deny("Blocked: command appears to transfer a credential-shaped file externally.")

    allow()


if __name__ == "__main__":
    main()
