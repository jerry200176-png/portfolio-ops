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

When the launched CLI exits, `agent-start` marks its session idle. Idle is not
task completion and does not make artifacts eligible. Only an explicit,
validated `terminal_success` lifecycle event can mark a task terminal; calling
`agent-finish` without such an event records `idle`. The bounded canary removes
only ignored `node_modules` backed by a package manifest and lockfile.
It never removes `.next`, `dist`, `build`, coverage, quarantine contents, or
unknown directories. It retains the worktree and user files, and skips active
sessions/leases, processes whose working directory or open files use the
worktree, incomplete process scans, tracked outputs, and quarantine. Repeating
it is safe.

Run `agent-finish --gc-dry-run` to inventory registered task worktrees. It
reports Linux free space, C: free space, artifact usage, and eligible reclaim.
Thresholds live in `config/artifact-gc.json`: PRESSURE below 50 GiB free and
CRITICAL below 30 GiB, leaving at least 30 GiB for Windows operational headroom.
This is an event hook and read-only report, not a background service. Reopened
worktrees stay protected while any process uses them. Installing the package
still requires the normal, separately approved rollout.

## Canonical lifecycle events

`agent-control` owns the portable lifecycle contract:

```json
{"task_id":"TASK-123","worktree":"/home/jerry/workspace/tasks/portfolio-ops/TASK-123","completion_state":"terminal_success","source":"exo","timestamp":"2026-09-24T10:00:00Z","session_id":"current-agent-control-session-id"}
```

Only `terminal_success` asks `agent-finish` to evaluate GC. `terminal_failed`,
`aborted`, and `idle` are recorded but never make artifacts eligible. The
existing process, session/lease, worktree, locked-package, and source/Git
checks still run. Events are bound to the current session id in the worktree
manifest, so a delayed event from a prior session cannot finish a reopened task.
The first successful terminal evaluation is also recorded once per session;
later idle callbacks or event replays cannot reclaim dependencies regenerated
after that completion.

For Exo, use the adapter **from outside the task worktree** so its own shell
does not count as active use:

```bash
agent-control/bin/exo-session-finish portfolio-ops TASK-123 -- \
  --summary "Task complete" --set-status done
```

The adapter runs the normal Exo command, checks its JSON result says both
`set_status=done` and `ticket_status=done`, then sends the event to
`agent-finish`. `keep` or `review` sends `idle`; failures and aborts never send
successful completion. Exo does not know about storage or GC. Other agents may
send the same JSON contract to `agent-finish <project> <task-id> --event-stdin`.

The installer records `.runtime-provenance.json` with version, source commit,
and UTC install time. `agent-control/bin/agent-finish --runtime-version` prints
those fields. The installer refuses modified agent-control source so that the SHA
names the code that was actually installed.
