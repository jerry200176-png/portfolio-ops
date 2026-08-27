# Workspace inventory — 2026-08-27

## Scope

Read-only inventory used these discovery roots:

- `/home/jerry/workspace`
- `/home/jerry/wt`
- `/home/jerry`
- `/home/jerry/workspace/tasks/alltrue`
- `/home/jerry/workspace/tasks/portfolio-ops`

The inventory found **222 candidate Git roots**, including **8 unresolved
paths**. The command did not fetch, reset, clean, move, delete, prune, or
modify any repository.

## Important findings

| Area | Current evidence | Operating decision |
|---|---|---|
| AllTrue canonical | `/home/jerry/workspace/AllTrue_System-clean`, `main`, dirty, local HEAD `1fac1143`, 279 commits behind its upstream ref | Preserve; never use as an implementation worktree |
| AllTrue user checkout | `/home/jerry/workspace/AllTrue_System`, dirty feature branch | Preserve all user changes |
| AllTrue task area | Many isolated task worktrees under `/home/jerry/workspace/tasks/alltrue`; current booking fix is `booking-regression-20260827` | Use one task directory per change; no cross-worktree edits |
| Sunrise canonical | `/home/jerry/workspace/sunrise-cafe`, dirty `chore/dependabot-major-policy` branch | Preserve; do not sync or clean in place |
| Portfolio control plane | `/home/jerry/workspace/portfolio-ops`, dedicated branch, clean at inventory time | All state updates go through an isolated Portfolio task worktree |
| Legacy / unresolved | `/home/jerry/alltrue`, `/home/jerry/alltrue-dashboard-v2`, and 8 unresolved candidates remain | Investigation-only; archive/removal requires explicit approval |

The read-only governance audit also passed 8/8 required controls for AllTrue,
8/8 for Sunrise, and 7/8 for Portfolio Ops. Portfolio Ops is missing only a
`LICENSE` artifact; that is tracked as a separate control-plane improvement,
not silently fabricated during this inventory refresh.

## Cleanup proposal artifact

The existing proposal-only tool was run against the three canonical/control
repositories. Its checksummed output is stored at
`/home/jerry/evidence/workspace-admin/phase3-cleanup-proposal/20260827T021924Z/`.
It proposes no automatic deletion: any unresolved or legacy path still needs
ownership, backup/recovery verification, and explicit approval before a later
archive or removal operation.

## Closed-loop rule

The folder problem is now represented as data instead of being silently
“cleaned up.” Every future task should record its repository, worktree, branch,
dirty state, source commit, PR, checks, deployment identity, and evidence
report. A later archive proposal may group abandoned worktrees, but it must
first prove ownership, recoverability, and that no dirty user work is lost.
