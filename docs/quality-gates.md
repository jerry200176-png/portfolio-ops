# Quality gates and decision boundaries

## Required gates

| Gate | Evidence | Stop condition |
|---|---|---|
| Inventory | path, remote, branch, HEAD, ahead/behind, status, worktrees, size, last activity | any repo cannot be identified unambiguously |
| Backup | bundle verification, working/staged diff, untracked list/archive, SHA-256 | any bundle, archive, or checksum fails |
| Fetch-only | pre/post HEAD/status/diff/worktree/ref snapshots | fetch tries to merge, rebase, prune, or rewrite |
| Proposal | keep/archive-candidate/remove-candidate with reason, risk, approval flag | proposal contains an unverified removal target |
| Verification | tests, shell syntax, diff check, forbidden-operation scan | any required check fails |

## Mandatory stop conditions

Stop immediately for a failed recovery artifact, checksum mismatch, missing
repository, unexpected working-tree change, credential or PII exposure,
ambiguous worktree ownership, or an action that would delete/move/rename,
reset/clean, merge/rebase, prune, force-push, deploy, or mutate production.

`prunable` is a review state only. The path, branch, HEAD, existence, process
references, and backup must be recorded before any Founder decision.

## Rollback

For file state, restore only from the verified untracked archive and recorded
working/staged diffs after confirming the target path and checksums. For Git
objects, use the verified bundle to recover refs into a new disposable clone or
integration worktree. Do not overwrite a canonical checkout as a rollback
shortcut. For policy/code changes, revert through a reviewed branch/PR; never
rewrite shared history.

## Founder decisions still required

- whether Portfolio Ops receives a legal `LICENSE` file;
- which GitHub ruleset and required checks become enforced on the default branch;
- whether any legacy/prunable worktree is archived or removed after impact review;
- whether `/home/jerry/alltrue` gets an integration worktree and which commits,
  if any, are intentionally retained;
- any deploy, production-data, credential, permission, or privacy action.
