# Workspace governance baseline report

Baseline date: 2026-08-01 Asia/Taipei. Remote refs were refreshed by the
previous fetch-only evidence run; no merge, rebase, reset, clean, prune,
remove, move, or delete was performed.

## Decision table

| Path | Classification | Reason | Risk | Approval |
|---|---|---|---|---|
| `/home/jerry/workspace/AllTrue_System-clean` | keep | canonical AllTrue checkout; currently clean | medium: behind remote | no for preservation; yes for integration/merge |
| `/home/jerry/workspace/sunrise-cafe` | keep | canonical Sunrise checkout; Dependabot file is dirty | high if overwritten | yes for changing/discarding dirty work |
| `/home/jerry/workspace/portfolio-ops` | keep | company control plane; report output is untracked | high if overwritten | yes for discarding reports |
| `/home/jerry/wt/sunrise-verify-fix` | keep | active verification worktree | medium | yes for lifecycle change |
| `/home/jerry/wt/alltrue-leave-1280` | keep | active task worktree with dirty documentation | high if overwritten | yes for lifecycle change |
| `/home/jerry/alltrue` | archive-candidate | legacy, dirty, severely divergent, and related to many worktrees | high; at least 14 prunable references require investigation | required |
| any unresolved `prunable` worktree | archive-candidate | Git cannot currently resolve its path; existence and external references are unknown | high | required |
| any path not in the manifest | remove-candidate | not yet part of the approved company workspace inventory | unknown until inventoried | required; no automatic action |

The labels are proposals, not commands. The authoritative generated proposal
format is produced by `scripts/phase3-cleanup-proposal.sh`.

## Current sync posture

- `/home/jerry/alltrue`: `main` is 1284 ahead and 1684 behind `origin/main`
  in the latest read-only observation; integration must happen in a new
  worktree.
- `/home/jerry/workspace/AllTrue_System-clean`: behind 134.
- `/home/jerry/workspace/sunrise-cafe`: behind 22 with an uncommitted
  `.github/dependabot.yml` change.
- `/home/jerry/wt/sunrise-verify-fix`: behind 38 and clean.
- `/home/jerry/workspace/portfolio-ops`: clean except untracked `reports/codex/`.
- `/home/jerry/wt/alltrue-leave-1280`: no upstream and has a modified
  documentation file.

These numbers are observations, not authorization to synchronize.
