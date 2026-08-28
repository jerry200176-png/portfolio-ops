# Workspace Cleanup Proposal

Status: proposal only. No checkout, worktree, branch, directory, or file was
archived, removed, moved, reset, cleaned, or overwritten as part of this
proposal.

## Capture

- Captured: 2026-08-28, Asia/Taipei
- Discovery roots: `/home/jerry/workspace`, `/home/jerry/wt`,
  `/home/jerry/actions-runner-alltrue`, and the bounded `/home/jerry` scan
- Inventory implementation: commit `df1f844`
- Inventory schema: 12 fixed-width tab-separated fields
- Latest scan digest: `a4349729ee086ebfe1974eeba78e674e82dfeefffc25b86540c705085ae9b5ec`
- Scan result: 290 Git-root rows, 265 task-worktree rows, 77 dirty rows, 11
  unresolved rows, and 0 malformed-width rows

The scanner is read-only. It does not fetch, prune, clean, move, delete,
reset, merge, rebase, or overwrite repositories.

## Candidate classification

### A. Already handled by this run

The following artifacts were created by this maintenance run and moved to the
desktop Trash with their checksums where available:

- temporary inventory TSVs and checksum files
- pytest caches created by verification
- temporary Python wrappers used to provide pytest to Exo
- adapter recovery backups

These are recoverable and are not cleanup targets for any other operator.

### B. Requires explicit owner approval

The manifest requires approval before archive or removal. The following roots
were dirty outside task worktrees:

| Role | Path | Dirty entries |
| --- | --- | ---: |
| canonical-checkout | `/home/jerry/workspace/AllTrue_System-clean` | 5 |
| canonical-checkout | `/home/jerry/workspace/sunrise-cafe` | 4 |
| control-plane | `/home/jerry/workspace/portfolio-ops` | 2 |
| legacy-checkout | `/home/jerry/actions-runner-alltrue/_work/AllTrue_System/AllTrue_System` | 1 |
| legacy-checkout | `/home/jerry/alltrue` | 22 |
| workspace-checkout | `/home/jerry/workspace/AllTrue_System` | 5 |
| task-worktrees | 265 rows, 38 dirty rows | 38 |

The 11 unresolved Git markers require identity and ownership resolution before
any action:

```text
/home/jerry/alltrue-ci867
/home/jerry/workspace/worktrees/alltrue-governance-contract-20260801
/home/jerry/workspace/worktrees/portfolio-governance-main-20260801
/home/jerry/workspace/worktrees/sunrise-governance-contract-20260801
/home/jerry/wt/alltrue-1264
/home/jerry/wt/alltrue-ci-budget
/home/jerry/wt/alltrue-cross-campus-parent
/home/jerry/wt/alltrue-liability-summary
/home/jerry/wt/alltrue-pi-thermal
/home/jerry/wt/alltrue-test-isolation
/home/jerry/wt/alltrue-upload-artifact-v7
```

### C. Do not treat as cleanup targets

- `.git` internal directories and markers
- dependency directories such as `node_modules` and `vendor`
- generated application directories such as Vite temp folders and scheduler
  evidence directories
- any dirty canonical, legacy, or task checkout until its owner confirms a
  recovery point
- secrets, credentials, production paths, and the workspace manifest itself

Empty directories found in the scan were confined to these protected or
dependency/generated locations; no ordinary empty workspace directory was
identified for safe removal.

## Required approval record

Before any future archive or removal, record all of the following for each
exact path:

1. path and repository/worktree identity;
2. owner confirmation and intended action (`archive` or `remove`);
3. clean/dirty status and a checksum or commit reference;
4. recovery destination and retention period; and
5. a post-action rescan proving that no unrelated path changed.

Until that record exists, the correct action is to leave the candidate in
place and update the inventory rather than mutate it.
