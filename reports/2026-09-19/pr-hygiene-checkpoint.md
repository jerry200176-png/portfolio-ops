# Existing PR hygiene checkpoint — 2026-09-19

Status: complete for the authorized PR-hygiene scope. This checkpoint records review and bounded maintenance only; it does not authorize or start a new In-App delivery phase.

## Window, scope, and coverage

- Census started: `2026-09-19T17:14:17+08:00`.
- Governed session started: `2026-09-19T17:15:26+08:00`.
- Audit/action checkpoint: `2026-09-19T17:36:00+08:00`.
- Coordinator session: `f627ab8f8ac14fc0af334550a3973a8e`; task `pr-hygiene-20260919`; `production_mutation=false`; preflight `pass`.
- Isolated worktree: `/home/jerry/workspace/tasks/portfolio-ops/pr-hygiene-20260919`; branch `chore/task-pr-hygiene-20260919`; starting base `d23f92e232a0df13f5b401ec648b8db2e03f15a3`.
- Coverage: 35/35 PRs that were open at census time, including every Draft. For each PR the latest body, paginated comments/reviews/files, actual diff, recorded base/head SHA, checks, issue/plan links, ownership evidence, and deployment path were inspected.

The effective repository scope comes from `portfolio.yaml` plus `governance/repository-governance.yaml`, not from the account-wide repository list:

| Repository | Why in scope | Open PRs, start → checkpoint |
|---|---|---:|
| `jerry200176-png/AllTrue_System` | registered, maintained product repo | 17 → 17 |
| `jerry200176-png/sunrise-cafe` | registered, maintained product repo | 8 → 8 |
| `jerry200176-png/portfolio-ops` | registered governance repo | 6 → 4 |
| `jerry200176-png/engineering-intelligence` | registered, maintained repo | 4 → 2 |
| `jerry200176-png/income-statement-app` | registered repo | 0 → 0 |
| `jerry200176-png/income-statement-app-releases` | registered repo | 0 → 0 |

Total open PR count changed from 35 to 31. `agent-control` has no registered GitHub repository, and `korea-trip-plan` currently has `github_repo: null`; both are outside the GitHub PR census. Unregistered and third-party repositories were not inspected or changed.

## Actions completed

1. `engineering-intelligence#71` was closed as redundant. Its only change was the 2026-09-03 daily report (`+34`); main already contains traceable replacements for 2026-09-04 (`ddfb99c087769f5b2125dc1e917f188d772774e8`, PR #74) and 2026-09-05 (`0537cbba439e45c4ae1b27d52145a03bb7bbfc91`, PR #77). Exact head `fb6ecf0a07e16d62941e39f09c4f3d7685ce79d3` passed manual Validate run `33740854283`; there were no reviews, live lease, session, or worktree. A closure comment preserves the replacement chain. The unmerged branch was retained.
2. `engineering-intelligence#78` was changed from Draft to Ready only after exact-head verification, then squash-merged into PR #1's feature branch. Pre-merge head `55dd054f35e4c354957dd0892d418d603fe917f2`; diff was one blank-line removal in the OpenAI-compatible adapter plus a 75-line evidence JSON; exact-head `validate` passed and there were no reviews or active owner/lease. Merge SHA: `7604a65f2029d8b7a7230cf2f9da023d62977d2c`. This did not target `main` and triggered no deployment. The branch was retained because its worktree contains an unrelated untracked `uv.lock`.
3. `portfolio-ops#40` was closed with an evidence comment pointing to replacement #69, while explicitly noting that #69 itself is not merge-ready. #40 head `b41a0b169318a5a0ee0da553e576ea5279c9ab82` had a failing `validate`, a duplicate manifest key, no review, and no active process/lease/worktree. The unmerged branch was retained.
4. `portfolio-ops#71` received the required `Risk-Class: R1`, rollback, and no-production-deploy declarations; GitHub updated it to current `main`, producing head `247c3f8ca1e4fbe95443ab7a0d9a83e557262c2c`. On that exact head `validate`, CodeQL, Secret scan, and governance-check passed; OpenSSF Scorecard was intentionally skipped by the private-repository workflow. With no reviews, unresolved threads, worktree, or lease, it was squash-merged as `3ee665b468949026a292500b150a79ec728b2617`. The Dependabot branch was deleted after merge; this is the only branch cleaned in this run. The merge changes three pinned `harden-runner` references for future security jobs and does not deploy a product.
5. `sunrise-cafe#349`, `#339`, and `#336` each received one bounded `@dependabot rebase` request. Their new exact heads all pass Agent Session Provenance, Lint & Build, and Playwright smoke. A PR comment records that they remain open because merging `main` invokes the production deploy-and-migrate workflow, the product overlay requires existing human/Founder authorization, and this goal grants no new production activation authority.

No force-push, direct push to `main`, `--admin`, production SSH, production activation, assertion weakening, allowlist widening, or fabricated provenance occurred.

Local verification for this checkpoint passed: `exo check`; 155 Python unit tests (one explicit live-integration skip) under `local-heavy-gate`; governance-contract validation; company-agent-contract validation; company-context validation; shell syntax checks; and `git diff --check`. The first local test invocation used the unavailable `python` executable and exited before running tests; it was corrected to the repository-supported `python3`, after which the complete suite passed.

## AllTrue_System — 17/17

Common evidence: audit-time `main` was `5d5c259c543fcafa1572d0d98f9281a8839dbda2`; the ruleset requires nine checks and resolved review threads, with zero mandatory approvals. None of the 17 exact heads has a `Deploy to Pi` run. Other than one old-head `COMMENTED` review on #2021, there are no GitHub review objects; Cursor quota messages are not reviews. Historical sessions/worktrees and owner comments remain coordination signals even where no live process or lease was found.

| PR | Head and diff | CI/review evidence | Disposition, owner/dependency, next step, deployment |
|---|---|---|---|
| #3046 | `6e5e51f5d1e0ff4f925feaf9980d6ee3edec5813`; `+1/-1`, OSV reusable workflow pin 2.5.1→2.6.0; behind 16 | Presubmit and Docs Integrity fail; provenance skipped; six pass; 0 reviews/comments | Retain. Dependabot-owned; add risk/tier/release/rollback, update from main, repair the Dependabot-compatible docs gate, rerun all checks. Merge changes production control-plane workflow behavior but does not directly deploy the app. |
| #3016 | `15863be3459d718515164458df85b02702531c44`; 15 files, `+666/-20`, capability grants/migration/acting mode/UI; DIRTY, behind 78 | Old head 9/9 pass; 0 reviews, 7 comments; historical session/worktree; owner says `PARKED / FOUNDER_REQUIRED` | Retain; no takeover. R3/T3 identity/authorization and schema decision needs Founder plus independent security review, conflict resolution and fresh CI. Merge would deploy app changes and run a production-schema migration even with the feature flag off. |
| #2981 | `8516814a4fd18aaa4d57ec0e09d3cf082b09f887`; 11 files, `+598/-10`, presence data/service/APIs/tests; DIRTY, behind 111 | Old head 9/9 pass; 0 reviews; 7 quota comments; issue #2809 and historical session/worktree | Blocked/retain. Reads are not bounded to a campus visible to the signed-in user, and concurrent arrivals with distinct idempotency keys can create two open presences. Fix authorization and a database/serialization invariant with tests; then conflict resolution, R3 review, Founder authorization and fresh CI. Merge would deploy backend/routes and a migration. |
| #2967 | `0906dcaf62fa95395e57b8e828139b9d61c9a4d8`; 8 files, `+573/-162`, staging docs/provisioning; DIRTY, behind 119 | Old head 9/9 pass; 0 reviews; historical Cursor session/worktree | Blocked/retain. Script prints the generated staging DB password, violating the secret-print machine ban; SQL quoting is also unsafe for arbitrary passwords. Replace with a safe handoff, add declarations, resolve conflicts and obtain fresh review/CI. No staging or production operation was run; the path is classified as application runtime and can create a deployment candidate. |
| #2849 | `bd88a5204a3d8118d5701d58b8ec11cf9879db87`; 10 files, `+964/-10`, receipt/recovery/deploy idempotency; DIRTY, behind 183 | Old head 9/9 pass; 0 reviews; R3/T3; historical session/worktree lacks model/profile | Blocked/retain. Receipt hard-codes only 3/9 required checks, mislabels any truthy `agent_cli` as Codex with null model, omits complete pagination, and can interpret a skipped deploy as successful activation. Correct the evidence model and independently review. Changes deploy workflow/runtime-classified scripts; Founder-gated. |
| #2833 | `9615abcc33dbac486ac78ab3c697d2772fd975f0`; 8 files, `+2131/-1335`, Laravel 12 candidate; behind 194 | PHPStan fails with 709 findings; eight other checks pass; 0 reviews; evidence in 9 comments | Retain as upgrade evidence, not mergeable. Requires separately approved, bounded typing remediation and current-main validation; do not weaken baselines. Merge would change the production backend framework/runtime and needs Founder decision. |
| #2679 Draft | `fa7a873d527565859295aa2b159403bda87d68f0`; 8 files, `+285/-59`, part-time payroll UI states/e2e; DIRTY, behind 296 | Provenance passes; eight required checks skipped; 0 reviews/comments; historical session/worktree | Retain as a low-risk repair candidate. Coordinate the historical owner, update normally, declare risk/tier/release/rollback, prove presentation-only scope, then obtain full fresh CI/review. Merge would deploy frontend. |
| #2677 | `0794b59b62fb4378be7483c4a60726019d7d9aa6`; 14 files, `+565/-76`, calendar leave/tail-session/billing behavior; DIRTY, behind 296 | Seven pass; PHPUnit/PHPStan skipped; 0 reviews; 4 retain comments | Retain. T3 product semantics still depend on Founder decisions; rebase, prove protected effects, independently review and rerun exact-head gates. Merge would deploy frontend behavior. |
| #2668 Draft | `c8f310ddd10d6b779e83de4b1d889ac2666c9adc`; 7 files, `+257/-19`, read-only binding-health UI/e2e; DIRTY, behind 300 | Provenance passes; eight required checks skipped; 0 reviews/comments; historical session/worktree | Retain as a low-risk repair candidate. Coordinate owner, update normally, complete declarations and full CI/review. Merge would deploy frontend. |
| #2661 Draft | `97c62c2628d41314c1c0e593f5cda149a7c6ded4`; 7 files, `+288/-60`, assessment UI/action surfaces; DIRTY, behind 302 | Provenance passes; eight skipped; 0 reviews, 3 owner findings; issue #1618/session/worktree | Blocked/retain. It deletes a valid non-empty native-button assertion while changing protected assessment actions. Restore or strengthen the assertion, split presentation-only work, add action regressions, update and rerun CI. Merge would deploy assessment frontend. |
| #2660 Draft | `69319c67700a5f2f044b4ccb70f4179392a427b1`; 5 files, `+204/-18`, LINE binding/unbind UI/e2e; DIRTY, behind 302 | Provenance passes; eight skipped; 0 reviews/comments; historical session/worktree | Retain. Identity-adjacent destructive action lacks request/permission/failure-boundary regression. Coordinate owner, update, add tests/declarations and rerun full gates. Merge would deploy frontend. |
| #2656 Draft | `4380a66c4754bce19fb59841a3e848ee1830a457`; 5 files, `+178/-38`, read-only reconciliation UI/a11y/e2e; DIRTY, behind 302 | Provenance passes; eight skipped; 0 reviews/comments; historical session/worktree | Retain as a low-risk repair candidate. Coordinate owner, update, add declarations and obtain fresh full CI/review. Merge would deploy frontend. |
| #2648 Draft | `f881e947e81d1bce5706bdf3eac82d9794240dc7`; 5 files, `+269/-42`, branch CRUD UI/e2e; DIRTY, behind 302 | Provenance passes; eight skipped; 0 reviews/comments; historical session/worktree | Retain. E2E covers edit-dialog and delete cancellation, not CRUD/permission/failure contracts. Update and add those regressions plus declarations and full review/CI. Merge would deploy frontend. |
| #2646 Draft | `8efedd3ec02fccca3027f3c3706198cf2ae23419`; 5 files, `+323/-139`, director accounts/approval/reset/delete UI; DIRTY, behind 302 | Provenance passes; eight skipped; 0 reviews/comments; historical session/worktree | Retain at T3/Founder boundary. Add identity, permission and destructive-action regression; update, declare risk and independently review with Founder authorization. Merge would deploy frontend. |
| #2626 Draft | `9590cb5e0b05923c369849c66f1ebba18abd3eba`; one PRD, `+365`; behind 315 | Provenance passes; eight skipped; 0 reviews; owner retain comment; unique plan artifact | Retain; do not implement in this goal. D1/D2, cross-period tail, billing and repair-manifest policy need Founder product/accounting decisions. Docs-only, so no app deployment, but merge would formalize undecided policy. |
| #2021 | `08c9e6dd84281b50a0698df1325574b7130250cb`; 12 files, `+679/-45`, contract split backend/API/UI/docs; DIRTY, behind 454 | Old head 9/9 pass; only review is old-head `COMMENTED`, not approval; 18 comments; owner retain evidence | Blocked/retain. Submit does not lock the StudentClass used by preflight, so concurrent submits can evade the pending PaymentReport invariant. Add consistent serialization and concurrent regression, then normal rebase, independent R3 review, Founder authorization and fresh CI. Merge changes billing and lesson settlement in production. |
| #1991 Draft | `87f0340a77c0d19d5de77dadda7e435b70870004`; 2 files, `+553/-5`, Learning Assessment spinout RFC/manifest; DIRTY, behind 459 | Provenance passes; eight skipped; 0 reviews, 6 decision comments; historical session, original worktree absent | Retain Draft. O1–O4/O7, learner auth, identity mapping and integration boundary need Founder decisions; unique RFC work prevents closure. Docs-only with no app deployment, but it is a major product/architecture decision. |

## sunrise-cafe — 8/8

Common evidence: ruleset requires strict `Lint & Build`, `Playwright smoke`, and `Agent Session Provenance`; no PR has a GitHub review. A merge to `main` starts `Production deploy and migrate`, including database migrations and Vercel deploy. The product overlay requires human/Founder merge approval, and this goal adds no production activation authority.

| PR | Head and diff | CI/review evidence | Disposition and next step |
|---|---|---|---|
| #350 | `0ed045d6f05b3fd78a8df9c1aa72e7f2ad340532`; package/lock, 9 grouped production dependencies, `+256/-305` | Lint & Build fails; Playwright skipped; 0 reviews; behind current main | Retain blocked. The grouped Stripe/React/Next/etc. update includes a Stripe API-version mismatch and other type errors. Split or repair without broadening scope, update normally, then fresh checks/review and explicit deployment approval. No production deployment observed. |
| #349 | `3d6f789d6db8e1555c61097dc6f09266c4bff19f`; package/lock dev group, `+62/-65` | Exact-head Agent Provenance, Lint & Build, Playwright all pass; runs `35434605964`/`35434605900`; 0 reviews; CLEAN | Retain pending the existing authorized approver and deployment window. Rebase evidence/comment recorded. Vercel preview was canceled by the ignored-build step; no production deployment observed. |
| #339 | `ca395b9ab2b0aa4265004efbe7c810f65be995ba`; Next 15.5.23→15.5.25, `+54/-42` | Exact-head three required checks pass; runs `35434595548`/`35434595554`; 0 reviews; CLEAN | Retain pending authorized approval/deployment window. Narrower than red grouped #350. No production deployment observed. |
| #338 | `b86884c61490acb4d09e7c94c8469b9bb4d35771`; Vitest 3.2.7→4.1.11, `+832/-808` | Lint & Build fails with JSX/parser suite failures; 0 reviews | Retain blocked major upgrade. Repair compatibility and rerun exact-head gates before a separately authorized deploy. No production deployment observed. |
| #337 | `23f3353cbe94ff52ab64068b49f8112c91c5c3ec`; title understates actual Vitest 3.2.6→5.0.0, `+808/-828` | Lint & Build fails with parsing failures; 0 reviews | Retain blocked; correct scope/title and repair the major upgrade before fresh review/CI and deployment approval. No production deployment observed. |
| #336 | `0e3854cb8b13bc1f679885f1f3a28d7456760dc4`; lockfile-only js-yaml 4.3.1→4.3.2, `+3/-3` | Exact-head three required checks pass; runs `35434560835`/`35434560839`; 0 reviews; CLEAN | Retain pending authorized approval/deployment window. Rebase evidence/comment recorded. No production deployment observed. |
| #323 | `50edc2d224151c54a72dec2834890a1d26796506`; 11 files, `+65/-35`, required typecheck and baseline repair | Old exact-head required checks pass; Cursor quota is NEUTRAL, not review; 0 reviews; CONFLICTING/DIRTY; linked #261 | Retain with historical owner/worktree. Owner must resolve conflicts narrowly, rerun current-head gates and obtain review/merge authorization. No takeover and no production deployment. |
| #307 Draft | `ea23e0f34dbf684cc43cafafcba094c9eaeb35`; 6 files, `+108/-8`, manual production approval gate/workflow | Old checks pass; 0 reviews; CONFLICTING/DIRTY; historical owner/worktree | Retain Draft. It changes production security/deployment policy and needs Founder decision; then owner resolves conflicts and obtains fresh gates. This run did not modify or invoke production. |

## portfolio-ops — 6/6 starting PRs

Common evidence: audit-time `main` was `d23f92e232a0df13f5b401ec648b8db2e03f15a3`. Required checks are `validate`, CodeQL, Secret scan, and OpenSSF Scorecard; review threads must be resolved and approvals required is zero. Scorecard `SKIPPED` is intentional for this private repo. The repo has no product deploy-on-push workflow.

| PR | Head and diff | CI/review/ownership evidence | Disposition and next step |
|---|---|---|---|
| #114 Draft | `b9d57721680182d4c15662e76867f3120321f7fe`; 8 files, `+502`, product-intelligence schema/data/proposals | Old required checks pass, Scorecard skipped; 0 reviews/comments; CubeLV author but no verifiable model/profile/run/session | Retain. Facts are stale (#3045 is already merged), Founder gates conflict with current policy, and competitor claims rely heavily on search snippets. Bind real provenance, refresh official/live/source evidence and GitHub/production facts, fix policy, add Risk-Class, update and independently review. No deployment. |
| #72 Draft | `fa83044ef1fcf1b7b324d04fb8eb8406ee68ce4a`; 11 files, `+291/-18`, evidence contract/identity/inventory/tests | Old checks pass; 0 reviews; dirty retained worktree/session; file budget/provenance mismatch and stale inventory | Retain. Rebuild unique contract/identity portions on current main, fix scope/provenance, add behavioral `UNKNOWN` identity tests and fresh inventory/checks. No deployment. |
| #71 | pre-update `73eff87…`; exact merge candidate `247c3f8ca1e4fbe95443ab7a0d9a83e557262c2c`; one file, `+3/-3`, three harden-runner pins | Exact-head validate/CodeQL/Secret scan/governance pass, Scorecard skipped; 0 reviews/threads; no lease/worktree | Squash-merged as `3ee665b468949026a292500b150a79ec728b2617`; Dependabot branch deleted. Changes future security jobs only; no product deployment. |
| #69 Draft | `dd7efc391c6e096dff2027c26b7fe31141a3dc02`; one file, `+28`, four workspace registrations | Old checks pass; 0 reviews; dirty retained worktree/session | Retain, not mergeable. Entries use superseded checkout policy and Korea's remote no longer resolves. Original owner must reconcile current registry/workspace truth or withdraw. No deployment. |
| #40 Draft | `b41a0b169318a5a0ee0da553e576ea5279c9ab82`; one file, `+28`, predecessor to #69 with duplicate key | `validate` fails; other old security checks pass; 0 reviews; no active lease/worktree | Closed as superseded by #69, with caveat that #69 still needs rework. Unmerged branch retained. No deployment. |
| #39 Draft | `428e86d7e4272a91f86796b132168ac349e7647a`; 2 files, `+49/-1`, ChatDev/MetaGPT research | Old required checks pass; 0 reviews/comments; dirty retained worktree/session has no model/profile | Retain. Sources are unpinned/stale and newer internal research only partially replaces unique ChatDev metadata. Refresh maintained source/tests and official status, or document an exact replacement mapping before closure. No deployment. |

## engineering-intelligence — 4/4 starting PRs

| PR | Head and diff | CI/review/ownership evidence | Disposition and next step |
|---|---|---|---|
| #79 Draft | `23aa5446e41f9b2ccfa9162254cd93711d569710`; 5 files, `+112`, optional OTel schema/docs/test/evidence | `validate` passes; 0 reviews/comments; dirty historical worktree; evidence embeds stale head and ticket remains `todo` | Retain. Owner must refresh self-evidence and authorization, reconcile current main and add a true behavioral test rather than only contract-string checks. No deployment. |
| #78 | pre-merge `55dd054f35e4c354957dd0892d418d603fe917f2`; adapter blank line plus 75-line evidence JSON | Exact-head `validate` passes; 0 reviews/comments; no live lease, but unrelated untracked `uv.lock` in worktree | Marked Ready and squash-merged into #1 branch as `7604a65f2029d8b7a7230cf2f9da023d62977d2c`. Not a main merge; no deployment. Branch retained. |
| #71 | `fb6ecf0a07e16d62941e39f09c4f3d7685ce79d3`; one obsolete daily report, `+34` | Manual Validate `33740854283` passes; 0 reviews; no active ownership | Closed as completely replaced by main commits for the following two daily reports. Branch retained because it was unmerged. No deployment. |
| #1 | now `7604a65f2029d8b7a7230cf2f9da023d62977d2c`; 348-file legacy LLM pipeline/generated corpus, originally `+7648/-3` | Fresh CI has not appeared after #78; previous head failed Ruff; 0 approvals; CONFLICTING/DIRTY | Retain. #78 repaired the one-line Ruff issue on the feature branch, but the branch still diverges massively from current main and contains unique adapter work mixed with stale generated bulk. Owner must rebase or split the unique adapter, then run fresh CI/review. No deployment. |

## Empty repositories

`income-statement-app` and `income-statement-app-releases` had zero open PRs at both census and checkpoint. Their paginated open-PR results were empty; no mutation or deployment occurred.

## Branch cleanup and ownership

The only deleted branch was `portfolio-ops`' merged Dependabot branch for #71. It was eligible because the PR was merged, its unique three-line change is present in merge `3ee665b…`, and there was no lease, worktree, owner process, or downstream dependency. No other branch satisfied all cleanup conditions:

- unmerged branches (#40 and EI #71 included) were retained;
- EI #78's worktree has unrelated untracked state;
- portfolio #39/#69/#72 and many AllTrue/Sunrise PRs retain dirty or historical worktrees/ownership signals;
- every remaining open PR has unique work, a blocker, or an explicit decision dependency.

## Model, router, and run evidence

- Local model cache exposes `gpt-5.6-sol` and `gpt-5.6-luna`. Machine routing maps protected/high-complexity reasoning to `sol`/architecture (`gpt-5.6-sol`) and the approved bounded writer profile to `luna`/implementation (`gpt-5.6-luna`). A dry run for high/root-cause/protected selected Sol with no fallback. A separate simple route selected Terra, confirming that a role or model nickname alone does not grant write authority.
- AllTrue audit run `/root/sol_alltrue_audit`: actual process command `codex -m gpt-5.6-sol -c model_reasoning_effort="high"`, PIDs `929636/929643`, started `2026-09-19T17:11:42+08:00`.
- Portfolio audit run `/root/sol_pr_audit`: same observed `gpt-5.6-sol` and `high` process evidence. The CLI did not carry a named `--profile`, so this report does not falsely label that run as an architecture-profile invocation.
- Bounded EI #78 worker `/root/luna_ei78`: explicitly dispatched as `gpt-5.6-luna`, effort `medium`, with approved local `implementation` profile; worktree `/home/jerry/workspace/tasks/engineering-intelligence/fix-pr1-validation-patch-20260905`.
- Coordinator/root's exact hosted model identifier is not exposed by the runtime and is therefore not claimed. Its authorization evidence is the agent-control session above, not a role name.

## Evidence gaps and Decision Delta

- Canonical agent-control preflight passed, but its fetch warned because another isolated worktree had local `main` checked out; this task was still created from current `origin/main`. No shared/forbidden checkout was edited.
- `exo brief` and later `exo check` pass in the task worktree, while `exo doctor` reports missing/drifted runtime directories. Exo remains experiment-only under the canonical bootstrap; it was not used to override agent-control.
- The installed agent-control `bin/` does not yet contain the just-merged `model-route-resolve`; the resolver was verified from the current portfolio task worktree. Documentation landing is not claimed as installed-runtime rollout.
- GitHub displayed fresh exact-head evidence for every executed merge. Older green checks are explicitly labeled old and are not treated as evidence for a changed candidate.

Founder decisions still required:

1. Sunrise #349/#339/#336 may be technically green, but an authorized human/Founder must approve the production deploy-and-migrate side effect and deployment window. This goal grants no such activation.
2. AllTrue R3/T3 or production-policy items (#3016, #2981, #2849, #2646, #2021, #1991, and product-policy #2626/#2677) require the recorded security/product/accounting decisions before implementation or merge.
3. Sunrise #307 requires a Founder decision on the production approval-gate design.

All other remaining PRs have a named owner signal or dependency, concrete evidence-based blocker, and a next step above. A blocked PR did not stop the rest of the run. No In-App report was marked production-verified or resolved.
