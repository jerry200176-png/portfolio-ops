@AGENTS.md
@governance/RULEBOOK.md

# Claude Code notes

- The two imports above are the rules. This file adds only Claude-specific mechanics.
- `.claude/settings.json` enforces part of the machine bans: a permission deny list, a Bash
  guard (`.claude/hooks/guard_bash.py`) and a Gmail trash/delete hook
  (`.claude/hooks/deny_tool.py`). They hold even under `bypassPermissions`. Never weaken them
  to finish a task; threat model in `docs/hook-threat-model.md`.
- Skills: `/portfolio-maintain <mode>` runs the portfolio SOP. Subagents live in
  `.claude/agents/`.
- Auto memory (`/memory`) is for debugging findings, environment details and preferences. Never
  write a safety rule there and never treat a memory entry as a bypass of a machine ban.
