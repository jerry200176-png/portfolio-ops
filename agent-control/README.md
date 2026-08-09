# Versioned agent-control gateway

This directory is the reproducible source for the workspace agent gateway.
The installed runtime is `/home/jerry/workspace/agent-control`; it is updated
only by the explicit installer in `scripts/install-agent-control.sh`.

The gateway supports `portfolio-ops`, `alltrue`, and `sunrise`. Each session
gets one task branch, an isolated worktree, a preflight result, and a manifest.
Production mutation is disabled by default. Existing sessions, logs, and
untracked user files are never removed by the installer.

```bash
scripts/install-agent-control.sh --apply
~/workspace/agent-control/bin/portfolio-agent-start --company <task-id> --claude
```
