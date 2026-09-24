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

When the launched CLI exits, `agent-start` marks its session idle and runs the
same safe cleanup hook. `agent-finish <project> <task-id>` is the explicit
task-terminal signal. Both keep the worktree and user files, and remove only ignored `node_modules`
with a matching package manifest/lockfile and ignored `.next` with a locked
Next.js build script. It skips live processes, live leases, unknown session
state, tracked outputs, and quarantined worktrees without owner/reason/time
metadata. Repeating it is safe.

Run `agent-finish --gc-dry-run` to inventory registered task worktrees. It
reports Linux free space, C: free space, artifact usage, and eligible reclaim.
Thresholds live in `config/artifact-gc.json`: PRESSURE below 50 GiB free and
CRITICAL below 30 GiB, leaving at least 30 GiB for Windows operational headroom.
This is an event hook and read-only report, not a background service. Reopened
worktrees stay protected while any process uses them. Installing the package
still requires the normal, separately approved rollout.
