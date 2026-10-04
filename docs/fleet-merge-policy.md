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
| Squash-merge low-risk reversible PR (R0–R1; scoped reversible R2) after **required** checks, if merge will not trigger production activation | **Yes** |
| Product deploy path that runs because `main` moved | **No** — Founder approval is required before production activation |
| `workflow_dispatch` of a **committed** reversible, non-production workflow already on default branch | **Yes** — record the run URL |
| Production migration execution, production deployment/activation, production data mutation, identity/permission/privacy/security policy, billing/payment semantics, material reservation/product policy, major data repair, destructive ops, major product direction | **No** — Founder approval |
| Author migration files and test locally / in authorized isolated environments | **Yes** — confirm environment isolation; never use production credentials |
| SSH / artisan / phpunit on the production host | **No** — machine ban |
| Force-push, history rewrite, `--admin` | **No** — machine ban |

## When the agent must merge

After opening the PR, wait until:

1. `Risk-Class: R0|R1|R2|R3` is in the PR body.
2. GitHub `mergeStateStatus` is `CLEAN` / mergeable.
3. Every **required** status check is `SUCCESS` (skipped is OK only when
   the workflow is designed to skip for this diff).
4. No unresolved review threads that the ruleset requires resolved.
5. Before merging or dispatching anything that would trigger production
   migration execution, deployment, or activation, require the explicit
   Founder decision record. The triggering merge/dispatch is part of the
   production side effect; do not use it to bypass the gate. For R3, attach a
   reviewed execution package with exact target/SHA, scope, current recovery
   point where applicable, compatibility, bounded operation, rollback or
   forward repair, and post-action probes. Stop if recovery or an essential
   control cannot be verified.
6. The diff does not print credential values or add a force-push / `--admin`
   bypass.
7. The change does not delete tests, lower assertions, broaden allowlists,
   or bypass security controls to pass CI.

Then: `gh pr merge --squash --delete-branch`. Do not `--admin`. Record the
merge SHA and runtime verification evidence.

If checks fail: fix in a new commit on the same branch; do not merge red.
If production verification fails after an approved deploy: stop further
mutation and surface the evidence; do not perform an additional production
rollback/activation without the required Founder decision or weaken gates.

## Risk classes (fleet)

| Class | Meaning | Merge / deploy |
|---|---|---|
| R0 | Docs, INDEX, radar, no production behavior | Agent merges after checks |
| R1 | Isolated fix; may include reversible migration authoring, but no production execution, authz/billing/security-policy change | Agent merges after checks only if merge does not trigger production activation |
| R2 | Scheduling/UX/API behavior that remains reversible with rollback | Agent merges after checks only if merge does not trigger production activation; production deploy still requires Founder |
| R3 / Founder-risk | Production migration execution/deployment, production data repair, destructive or direction-locking migration design, breaking schema contract with material blast radius, privilege/security policy, billing/payment semantics, material reservation policy, destructive ops, major product direction/architecture | Code and migration may be prepared/tested as PR; **production activation/mutation requires Founder** |

When unsure between R1 and R2, declare R2. When unsure whether Founder risk
applies, treat it as Founder-risk and stop before the production side effect or
irreversible design decision.

## What is not “acceptance”

- Chat LGTM, Draft PR text, or “tests passed on my laptop” without the
  required GitHub check.
- Admin merge to bypass a failing required check.
- Merging a second repository in the same session.
- Claiming deploy success without health/version identity evidence.

## After merge

Close the GitHub issue when the product Evidence Contract is satisfied
(AllTrue in-app bugs: public reporter reply still required). Read-only confirm
the expected Actions/deploy and runtime identity; production deployment or
rollback still requires the Founder decision. Dispatch follow-up committed
**reversible, non-production** workflows if that was the task.

## Rollback

R0/R1/R2: revert the commit; any production rollback or re-activation follows
the same Founder approval boundary as production deployment.
Founder-risk: use the approved Repair Manifest / Founder-directed path only.
