# Portable Claude hooks — 2026-07-27

## Problem
`.claude/settings.json` hardcoded `/home/jerry/workspace/portfolio-ops/.claude/hooks/*.py`.
Cloud Agents and alternate checkouts could not load PreToolUse hooks → Graph Engineering blocked.

## Fix
Use `python3 "${CLAUDE_PROJECT_DIR:-.}/.claude/hooks/..."`.

## Verify
```bash
python3 .claude/hooks/test_guard_bash.py
# then reload hooks in a fresh Claude Code / Cloud session
```

## Out of scope
Cursor Orchestrator API key verification (`CURSOR_ORCHESTRATOR_API_KEY` → `/v0/me`) remains a separate Founder credential step.
