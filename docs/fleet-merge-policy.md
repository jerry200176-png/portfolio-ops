# Fleet merge policy

**Canonical owner:** portfolio-ops (`governance/AUTONOMY_POLICY.md` is the
capability table; this file is the merge procedure).  
**Founder decision:** 2026-08-15 — a human rubber-stamp of CI the Founder
does not re-derive is not a control. Required GitHub checks are the
acceptance. Agents squash-merge when those checks are green.

Product repositories (AllTrue, Sunrise, others) **do not override** this
capability table. They may add **stricter required checks** and domain P0
bans (no Pi tests, campus isolation). They may not re-ban merge after those
gates pass.

## Merge vs deploy

| Action | Autonomous after gates? |
|---|---|
| Squash-merge a PR whose **required** checks are green | **Yes** |
| AllTrue `deploy.yml` running *because* `main` moved (including skipping docs-only) | **Yes, as a consequence of merge** — that workflow remains the only production execute path (contract I1) |
| Extra production mutation: `workflow_dispatch` rotations, Pi artisan, Repair Manifest, Vercel prod click, paid-plan changes | **No** — Founder |
| Force-push, history rewrite, credential print/rotate, Gmail send, issue close | **No** — Founder |

If merging a **code** PR to AllTrue `main` will start `deploy.yml`, that is
accepted. The Founder already did that click without re-running the suite.
The checks are the acceptance; do not wait for a second human who will not
read them.

## When the agent must merge

After opening the PR, wait until:

1. `Risk-Class: R0|R1|R2` is in the PR body (R3: stop; Founder only).
2. GitHub `mergeStateStatus` is `CLEAN` / mergeable.
3. Every **required** status check is `SUCCESS` (skipped is OK only when
   the workflow is designed to skip for this diff, e.g. docs-only PHPUnit).
4. No unresolved review threads that the ruleset requires resolved.
5. The diff does not add Founder-only work (credential values, force-push
   scripts, enabling a previously disabled autonomous-loop workflow).

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
| R3 | Production data repair, privilege expansion, mass recalculation, enabling autonomous-loop, credential rotation | **Founder** |

When unsure between R1 and R2, declare R2. When unsure between R2 and R3,
declare R3 and stop.

## What is not “acceptance”

- Chat LGTM, Draft PR text, or “tests passed on my laptop” without the
  required GitHub check.
- Admin merge to bypass a failing required check.
- Merging a second repository in the same session.

## Rollback

R0/R1: revert commit. R2: revert or prior deploy SHA via the product
control plane (Founder if that control plane is a dispatch/repair, not a
normal `deploy.yml` on merge). R3: Repair Manifest only.
