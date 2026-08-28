# Workspace inventory evidence — 2026-08-28

The safe inventory script was run against `/home/jerry/workspace` and
`/home/jerry`. It recorded state without reset, clean, stash, merge, rebase,
prune, deletion, or file mutation in any existing checkout.

## `/home/jerry/workspace` repository roots

| Path | Role | Branch | HEAD | Dirty | Ahead/behind |
|---|---|---|---|---:|---:|
| `workspace/AllTrue_System-clean` | canonical checkout | `main` | `1fac1143` | yes | behind 279 |
| `workspace/AllTrue_System` | workspace checkout | `chore/task-receipt-image-copy-20260825` | `71bc0699` | yes | behind 19 |
| `workspace/engineering-intelligence` | workspace checkout | `codex/persist-task-evidence-contract` | `c30ab43a` | no | 0 / 0 |
| `workspace/income-statement-app` | workspace checkout | `main` | `0f70d64d` | no | 0 / 0 |
| `workspace/income-statement-app-releases` | workspace checkout | `main` | `0946db23` | no | 0 / 0 |
| `workspace/korea-trip-plan` | workspace checkout | `main` | `ee2594b0` | no | 0 / 0; remote unreachable in GitHub listing |
| `workspace/portfolio-ops` | control plane | `chore/2026-08-22-p0-sweep` | `b1686e94` | yes | 0 / 0 |
| `workspace/sunrise-cafe` | canonical checkout | `chore/dependabot-major-policy` | `773ea48c` | yes | behind 45 |

The ninth row is the current isolated Portfolio Ops task worktree created for
this report. The AllTrue UI task worktree is listed separately in its own
session manifest and is based on the current `origin/main` SHA
`4a146e262db6f330e97d2d9f2777367239246225`.

## Legacy paths

| Path | Role | State | Rule |
|---|---|---|---|
| `/home/jerry/alltrue` | legacy AllTrue checkout | dirty, diverged | never edit |
| `/home/jerry/alltrue-dashboard-v2` | legacy AllTrue checkout | clean, diverged | evidence-only |
| `/home/jerry/alltrue-ci867` | unresolved legacy candidate | git root unresolved by inventory | preserve and investigate only |

## Decision

Use isolated task worktrees for every new change. Existing dirty or diverged
checkouts are preserved exactly as found; no cleanup proposal is authorized by
this snapshot.
