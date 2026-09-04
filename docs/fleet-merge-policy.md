# Fleet merge policy

**Canonical owner:** portfolio-ops (`governance/AUTONOMY_POLICY.md` is the
capability table; this file is the merge procedure).  
**Operator:** the implementing Agent for low-risk reversible work.

Product repositories may add **stricter required checks** and domain P0
bans. They may not add a Founder rubber-stamp for docs/UI/small reversible
fixes.

## Merge vs deploy vs Founder risk

| Action | Autonomous after gates? |
|---|---|
| Squash-merge low-risk reversible PR (R0–R1; scoped reversible R2) after **required** checks | **Yes** |
| Product deploy path that runs because `main` moved (risk class allows it) | **Yes** — deploy is not itself a Founder gate |
| `workflow_dispatch` of a **committed** reversible workflow already on default branch | **Yes** — record the run URL |
| Production data mutation, irreversible migration, identity/permission/security policy, billing, major data repair, destructive ops, major product direction, activation without reliable rollback | **No** — Founder approval |
| SSH / artisan / phpunit on the production host | **No** — machine ban |
| Force-push, history rewrite, `--admin` | **No** — machine ban |

## When the agent must merge

After opening the PR, wait until:

1. `Risk-Class: R0|R1|R2|R3` is in the PR body.
2. GitHub `mergeStateStatus` is `CLEAN` / mergeable.
3. Every **required** status check is `SUCCESS` (skipped is OK only when
   the workflow is designed to skip for this diff).
4. No unresolved review threads that the ruleset requires resolved.
5. R3 / Founder-risk classes include an explicit Founder decision record
   before any irreversible activation. Do not merge irreversible production
   activation on chat claims alone.
6. The diff does not print credential values or add a force-push / `--admin`
   bypass.
7. The change does not delete tests, lower assertions, broaden allowlists,
   or bypass security controls to pass CI.

Then: `gh pr merge --squash --delete-branch`. Do not `--admin`. Record the
merge SHA and runtime verification evidence.

If checks fail: fix in a new commit on the same branch; do not merge red.
If production verification fails after deploy: stop further mutation,
rollback/report through the product path, and do not lower gates.

## Risk classes (fleet)

| Class | Meaning | Merge / deploy |
|---|---|---|
| R0 | Docs, INDEX, radar, no production behavior | Agent merges after checks |
| R1 | Isolated fix, no migration/authz/billing/security-policy change | Agent merges + deploys after checks |
| R2 | Scheduling/UX/API behavior that remains reversible with rollback | Agent merges + deploys after checks |
| R3 / Founder-risk | Production data repair, irreversible migration, privilege/security policy, billing rules, destructive ops, activation without reliable rollback | Code may be prepared as PR; **activation/mutation requires Founder** |

When unsure between R1 and R2, declare R2. When unsure whether Founder risk
applies, treat it as Founder-risk and stop before irreversible activation.

## What is not “acceptance”

- Chat LGTM, Draft PR text, or “tests passed on my laptop” without the
  required GitHub check.
- Admin merge to bypass a failing required check.
- Merging a second repository in the same session.
- Claiming deploy success without health/version identity evidence.

## After merge

Close the GitHub issue when the product Evidence Contract is satisfied
(AllTrue in-app bugs: public reporter reply still required). Confirm
deploy/Actions and runtime identity. Dispatch follow-up committed
**reversible** workflows if that was the task.

## Rollback

R0/R1/R2: revert commit or prior deploy SHA via the product control plane.
Founder-risk: use the approved Repair Manifest / Founder-directed path only.
