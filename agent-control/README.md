# Versioned agent-control gateway

This directory is the reproducible source for the workspace agent gateway.
The installed runtime is `/home/jerry/workspace/agent-control`; it is updated
only by the explicit installer in `scripts/install-agent-control.sh`.

The gateway supports `portfolio-ops`, `alltrue`, and `sunrise`. Each session
gets one task branch, an isolated worktree, a preflight result, and a manifest.
Production mutation is disabled by default. Existing sessions, logs, and
untracked user files are never removed by the installer.

`--dry-run` prints a plan from the already cached `origin/main` ref. It does
not fetch, create directories or worktrees, change refs, write a session
manifest, acquire a lock, or append a launch log. If the cached ref is absent,
the preview fails without refreshing it; a normal launch performs fetch and
preflight.

```bash
scripts/install-agent-control.sh --apply
~/workspace/agent-control/bin/portfolio-agent-start --company <task-id> --claude
```
