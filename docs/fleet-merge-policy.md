# Fleet merge policy

**Canonical owner:** portfolio-ops (`governance/AUTONOMY_POLICY.md` is the
capability table; this file is the merge procedure).  
**Operator:** the implementing Agent. The owner is not an approval queue.

Product repositories (AllTrue, Sunrise, others) **do not override** this
capability table. They may add **stricter required checks** and domain P0
bans (no Pi tests, campus isolation). They may not add a Founder
rubber-stamp.

## Merge vs deploy vs extra mutation

| Action | Autonomous after gates? |
|---|---|
| Squash-merge a PR whose **required** checks are green (R0–R3) | **Yes** |
| AllTrue `deploy.yml` running *because* `main` moved | **Yes** — product control plane (I1) |
| `workflow_dispatch` of a workflow **already on** the default branch | **Yes** — Agent fills inputs; records the run URL |
| SSH / artisan / phpunit on the production host | **No** — machine ban |
| Force-push, history rewrite, `--admin` | **No** — machine ban |

## When the agent must merge

After opening the PR, wait until:

1. `Risk-Class: R0|R1|R2|R3` is in the PR body.
2. GitHub `mergeStateStatus` is `CLEAN` / mergeable.
3. Every **required** status check is `SUCCESS` (skipped is OK only when
   the workflow is designed to skip for this diff, e.g. docs-only PHPUnit).
4. No unresolved review threads that the ruleset requires resolved.
5. R3: Repair Manifest or execution package is **in the diff or a linked
   committed path**, with backup/recovery point and blast radius. Do not
   merge R3 on chat claims alone.
6. The diff does not print credential values or add a force-push / `--admin`
   bypass.

Then: `gh pr merge --squash --delete-branch`. Do not `--admin`. Do not
skip hooks. Record the merge SHA in the session note.

If checks fail: fix in a new commit on the same branch; do not merge red.

## Risk classes (fleet)

Same letters as AllTrue’s table; meaning is fleet-wide:

| Class | Meaning | Merge |
|---|---|---|
| R0 | Docs, INDEX, radar, no production behavior | After checks, agent merges |
| R1 | Isolated fix, no migration/authz/billing/deploy-workflow change | After checks, agent merges |
| R2 | Scheduling, billing, authz, schema, deploy workflow, major deps | After checks, agent merges |
| R3 | Production data repair, privilege expansion, mass recalculation, credential rotation workflow | After checks **and** Repair Manifest / execution package, agent merges |

When unsure between R1 and R2, declare R2. When unsure between R2 and R3,
declare R3 and include the manifest; do not stop for a human click.

## What is not “acceptance”

- Chat LGTM, Draft PR text, or “tests passed on my laptop” without the
  required GitHub check.
- Admin merge to bypass a failing required check.
- Merging a second repository in the same session.

## After merge

Close the GitHub issue when the product Evidence Contract is satisfied
(AllTrue in-app bugs: public reporter reply still required). Confirm
deploy/Actions. Dispatch follow-up committed workflows if that was the
task.

## Rollback

R0/R1: revert commit. R2: revert or prior deploy SHA via the product
control plane (Agent opens the revert PR or dispatches the product
rollback workflow). R3: Repair Manifest rollback path.
