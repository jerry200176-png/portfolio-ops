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

### Exact scoped artifact maintenance

`bin/agent-artifact-maintenance --plan PLAN.json --dry-run-receipt RECEIPT.json`
checks one explicitly named AllTrue artifact. Repeat with `--apply` only after
reviewing the successful receipt. The ordinary node_modules canary and terminal
completion claims are unchanged. This entry point never changes session states.

The plan binds `worktree`, `task_id`, `session_id`, `category`, `target`,
`source_tree` (the committed backend/frontend tree object), `source_files`
(path → SHA256 for the tracked package manifest and lockfiles), `pristine`
(an isolated rebuilt directory outside task roots), `pristine_digest`,
`rebuild_command`, `rebuild_evidence`, and `retained_evidence`. Evidence arrays
contain `{ "path": "/absolute/file", "sha256": "…" }` records. The operator
must retain the actual successful rebuild log and needed acceptance evidence;
this tool does not execute arbitrary rebuild commands or infer acceptance.

Supported exact paths are backend/vendor (composer_vendor), frontend/dist_build
(build_output), and frontend/node_modules/.vite or .vite-temp (tool_cache).
Other paths are rejected. Pristine must match every regular file, directory and
mode; links, special files and multiply linked files are rejected. Differing
Composer generated files are not silently exempted. Proving only package names
or a lockfile is insufficient. Cache content which cannot be independently
reproduced remains untouched.

Identity must match canonical registry and worktree manifests. Registry state
must be idle or terminal, with no active lease or process; idle alone provides
no eligibility. Full process visibility, exact proof, ignored/untracked target,
unchanged tracked source, retained evidence and no registered-worktree symlink
references are required. Existing lifecycle locks serialize the check/removal
with agent-start for the target and registered peers. Worktree inventory is
rechecked before removal. The successful dry-run receipt binds the exact plan;
apply repeats all checks. The report counts file allocated blocks using the
same existing GC helper; whole-root net change must be measured separately.

This mechanism cannot arbitrate ungoverned external writers; such activity must
be excluded by the operator. It never deletes source, Git, backend storage,
whole worktrees, or lifecycle metadata. Permission/read failures skip the target.

For Composer only, `package_digests` may map exact locked `namespace/package`
names to pristine digests instead of matching the whole vendor directory.
Each requested name must occur in composer.lock and each package directory
must independently match the rebuilt package. All checks execute once under
the same locks, before any package is removed. The receipt enumerates exact
package targets. Generated vendor/composer metadata, bins, root files and
unrequested packages remain intact; differing generated metadata is therefore
never deleted or rewritten to manufacture an exact match. A later locked
Composer install rebuilds removed packages. Invalid names, traversal,
unlocked names, shared links and modified package files reject the batch.

Apply takes another complete process snapshot and repeats the complete
identity/lease/source/lock/evidence/pristine/shared-reference verification.
After that potentially slow proof work, it takes a final fresh process snapshot
and rechecks identity/lifecycle/lease immediately before each exact deletion.
Thus a worker or lease that appears during hashing prevents removal. Locks
serialize only canonical agent-start; they do not guarantee control of unknown
or unmanaged writers. Observed activity skips the target; if an unmanaged writer
cannot be excluded, the operator must not activate maintenance.
