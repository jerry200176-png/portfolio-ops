# CEO Dashboard

## 2026-08-29 — DirectorDashboard view switcher live

- AllTrue PR [#2167](https://github.com/jerry200176-png/AllTrue_System/pull/2167)
  is squash-merged as `992ea7341228aec142ce6e023d1d5d44fce0f1c9`. The 主任總覽
  「今天／完整營運」 switcher now explicitly connects each tab to its labelled,
  keyboard-focusable work area. Existing task-first, lazy-load, data, permission,
  and operational behavior is unchanged.
- Targeted Vitest passed 8/8; DirectorDashboard UI foundation E2E passed 7/7
  across 390/412/768/1280/1440px. Required PR checks and main CI
  [33206113693](https://github.com/jerry200176-png/AllTrue_System/actions/runs/33206113693)
  passed; Deploy to Pi
  [33206406490](https://github.com/jerry200176-png/AllTrue_System/actions/runs/33206406490)
  and read-only acceptance
  [33206683512](https://github.com/jerry200176-png/AllTrue_System/actions/runs/33206683512)
  also passed.
- Production health is `status=ok`; `/version.json` and `/deployment.json` both
  report `992ea7341228aec142ce6e023d1d5d44fce0f1c9`. The broader #2135 convergence
  remains active, and LearningRecords #1621 stays behind the #957/#1080 data-truth gate.

## 2026-08-29 — StudentsList row disclosure live

- AllTrue PR [#2166](https://github.com/jerry200176-png/AllTrue_System/pull/2166)
  is squash-merged as `3251e6c476887ceb432e198462fd8e34a5347577`. StudentsList
  rows now support Enter/Space expansion, expose an explicit relationship to
  the course detail row, and isolate selection/edit/delete controls from the
  row-level keyboard handler. Student/course/payment data, permissions, and
  navigation behavior are unchanged.
- Local targeted StudentsList tests passed 12/12, the complete real-Vue UI
  foundation suite passed 139/139, and required PR checks passed. Main CI
  [33203497304](https://github.com/jerry200176-png/AllTrue_System/actions/runs/33203497304),
  Deploy to Pi
  [33203794209](https://github.com/jerry200176-png/AllTrue_System/actions/runs/33203794209),
  and read-only production acceptance
  [33204061441](https://github.com/jerry200176-png/AllTrue_System/actions/runs/33204061441)
  passed.
- Production `/api/v1/health` returned `ok`; `/version.json` reports build
  SHA `3251e6c476887ceb432e198462fd8e34a5347577`. Evidence is recorded on
  the [StudentsList rollout issue #692](https://github.com/jerry200176-png/AllTrue_System/issues/692).
- The broader rollout remains active: the current six-repository inventory is
  76 open issues and 15 open PRs, with five existing open AllTrue PRs; #2166
  is merged. No claim is made that the entire UI/UX goal or the StudentsList
  rollout is complete.

## 2026-08-29 — CourseManagement interaction hierarchy live

- AllTrue PR [#2165](https://github.com/jerry200176-png/AllTrue_System/pull/2165)
  is squash-merged as `88c4d95388aec6fb9fcda039c43230b1baeb3057`. The course
  lookup page now separates student-group disclosure from the student-focus
  action and gives course/billing tabs plus history disclosure explicit
  keyboard and screen-reader relationships. Existing course, billing,
  scheduling, permission, and navigation behavior is unchanged.
- Local CourseManagement tests passed 18/18, the targeted pilot E2E passed
  6/6, and the complete real-Vue UI foundation suite passed 139/139 across
  mobile and desktop widths. Required PR checks, main CI
  [33201485946](https://github.com/jerry200176-png/AllTrue_System/actions/runs/33201485946),
  Deploy to Pi
  [33201790150](https://github.com/jerry200176-png/AllTrue_System/actions/runs/33201790150),
  and read-only production acceptance
  [33202081650](https://github.com/jerry200176-png/AllTrue_System/actions/runs/33202081650)
  passed.
- Production `/api/v1/health` returned `ok`; `/version.json` reports build
  SHA `88c4d95388aec6fb9fcda039c43230b1baeb3057`. The release evidence is
  recorded on [AllTrue issue #691](https://github.com/jerry200176-png/AllTrue_System/issues/691#issuecomment-5456611507).
- Issue [#2007](https://github.com/jerry200176-png/AllTrue_System/issues/2007)
  remains open for later IA work. The current six-repository inventory is 76
  open issues and 15 open PRs; the five AllTrue open PRs are existing work,
  while #2165 is merged.

## 2026-08-29 — Student course detail disclosure live

- AllTrue PR [#2164](https://github.com/jerry200176-png/AllTrue_System/pull/2164)
  is squash-merged as `350da457ec9010aca90d2e718b0055cd77156b86`. The selected
  course is now an explicit `目前課程工作區`; historical courses remain a
  separate accessible disclosure. The release also fixed the real history
  lookup bug where the disclosure reused the active-only course collection.
- Main CI
  [33198942210](https://github.com/jerry200176-png/AllTrue_System/actions/runs/33198942210),
  Deploy to Pi
  [33199257475](https://github.com/jerry200176-png/AllTrue_System/actions/runs/33199257475),
  and read-only production acceptance
  [33199540861](https://github.com/jerry200176-png/AllTrue_System/actions/runs/33199540861)
  passed. Production `/version.json` matched `350da457` and health returned
  `ok`.
- AllTrue issue [#2007](https://github.com/jerry200176-png/AllTrue_System/issues/2007)
  remains open for the remaining course IA rollout. Current six-repository
  inventory is 76 open issues and 15 open PRs: AllTrue 70/5, Portfolio Ops
  2/6, Engineering Intelligence 0/1, Sunrise Cafe 4/3, and both Income
  Statement repos 0/0.

## 2026-08-29 — Teacher workbench next action live

- AllTrue PR [#2163](https://github.com/jerry200176-png/AllTrue_System/pull/2163)
  is squash-merged as `31795f9b6a7be7523a4b4b69358cf1a61ba135c1`. TeacherHome
  now makes the existing highest-priority task the single `現在先做` action,
  while later tasks remain under `接著處理`; existing data, routing,
  permissions, and leave filtering are unchanged.
- Main CI
  [33196785637](https://github.com/jerry200176-png/AllTrue_System/actions/runs/33196785637),
  Deploy to Pi
  [33196933804](https://github.com/jerry200176-png/AllTrue_System/actions/runs/33196933804),
  and read-only production acceptance
  [33197207380](https://github.com/jerry200176-png/AllTrue_System/actions/runs/33197207380)
  passed. Production version build SHA and health matched the merge SHA.
- Issue [#1618](https://github.com/jerry200176-png/AllTrue_System/issues/1618)
  remains open for the broader teacher daily-workflow follow-up. Current
  six-repository inventory is 76 open issues and 15 open PRs: AllTrue 70/5,
  Portfolio Ops 2/6, Engineering Intelligence 0/1, Sunrise Cafe 4/3, and
  both Income Statement repos 0/0.

## 2026-08-29 — Student course overview Phase 2A live

- AllTrue PR [#2162](https://github.com/jerry200176-png/AllTrue_System/pull/2162)
  is squash-merged as `a567f55e9a43d2214161347083a6e5d77067b5d6`. It adds the
  student course overview, attention-first active-course selection, focused
  detail card, and mobile table-scroll preservation. It is frontend-only:
  existing course actions, API payloads, permissions, attendance, billing,
  scheduling, and data ownership are unchanged.
- Main CI [33194188998](https://github.com/jerry200176-png/AllTrue_System/actions/runs/33194188998),
  Deploy to Pi [33194481228](https://github.com/jerry200176-png/AllTrue_System/actions/runs/33194481228),
  and read-only Calendar/Course Production Acceptance
  [33194768520](https://github.com/jerry200176-png/AllTrue_System/actions/runs/33194768520)
  passed. Production reports build SHA `a567f55e` and health `ok`.
- AllTrue #2007 was reopened after GitHub auto-closed it from the PR keyword;
  the parent issue intentionally remains open for later IA phases. The current
  cross-repo inventory is 76 open issues and 15 open PRs: AllTrue 70/5,
  Portfolio Ops 2/6, Engineering Intelligence 0/1, Sunrise Cafe 4/3, and
  both Income Statement repos 0/0.
- This is the next bounded UX slice in the hybrid direction: warmer learning
  moments remain contained, while billing, attendance, PII, and other
  safety-critical surfaces stay professional and explicit. PR #2129 remains
  blocked by failed Presubmit/UI Smoke and its 1,279-line diff.

## 2026-08-29 — Student course IA proposal ready for review

- AllTrue PR [#2161](https://github.com/jerry200176-png/AllTrue_System/pull/2161)
  merged the proposal-only redesign for issue
  [#2007](https://github.com/jerry200176-png/AllTrue_System/issues/2007).
  The proposal adds desktop/mobile wireframes, status ordering, responsive and
  accessibility acceptance, and a two-level course workspace that makes the
  next safe action visible without turning the director workflow into a game.
- The direction is explicit: bank-like clarity for billing, attendance, PII,
  delete, close, and other high-risk work; contained learning warmth only where
  it helps a learning-oriented journey. No production code or data changed in
  this PR, and #2007 remains open pending product/director review.
- The open PR register still has five AllTrue PRs. PR #2129 remains blocked by
  failed Presubmit/UI Smoke and its 1,279-line diff; it is not a release
  candidate. PR #2161 is merged and now the review gate for the next #2007
  implementation slice.
- Portfolio Ops PR #51 is the current merged inventory record; superseded PR
  #50 is closed. The canonical Portfolio Ops checkout and other dirty user
  worktrees were preserved.

## 2026-08-29 — AllTrue visual companion slice and acceptance recovery

- AllTrue PR [#2159](https://github.com/jerry200176-png/AllTrue_System/pull/2159)
  fixed the Calendar/Course production acceptance contract by targeting the
  current semantic `AtPageHeader` headings. It merged as
  `96d2980aa8d93a88ea56fdb0b1ca8a5a980eca06`; corrected read-only acceptance
  [33188606426](https://github.com/jerry200176-png/AllTrue_System/actions/runs/33188606426)
  passed desktop and mobile parity checks.
- AllTrue PR [#2160](https://github.com/jerry200176-png/AllTrue_System/pull/2160)
  adds the first genuine visual-direction slice: an original image-model
  learning companion, warm amber/navy surface, rounded hierarchy, encouraging
  copy, and a real queue link on TeacherHome. It deliberately keeps billing,
  attendance, PII, scheduling, permissions, and operational data unchanged.
- PR #2160 merged as `f29ad8a36f5dd5780a6c6b0d8baae85b322d99fb`. Main CI
  [33189424753](https://github.com/jerry200176-png/AllTrue_System/actions/runs/33189424753),
  deploy [33189578837](https://github.com/jerry200176-png/AllTrue_System/actions/runs/33189578837),
  production `version.json`, and `/api/v1/health` all passed. Local real-Vue
  evidence passed five normal/empty/error and responsive TeacherHome cases.
- This is an intentional hybrid direction: Duolingo-like warmth and emotional
  feedback in learning-oriented moments, with bank-like restraint and explicit
  states on safety/data-heavy operations pages. It is the beginning of the
  visual system, not a claim that the entire app has already been redesigned.
- Fresh GitHub inventory remains six owner-visible repositories with 76 open
  issues and 16 open PRs: AllTrue 70/5, Portfolio Ops 2/7, Engineering
  Intelligence 0/1, Sunrise Cafe 4/3, and both Income Statement repos 0/0.
- Portfolio state and evidence were refreshed in
  [`reports/2026-08-28/github-triage.md`](reports/2026-08-28/github-triage.md)
  and [`state/work-queue.yaml`](state/work-queue.yaml). Existing dirty
  canonical worktrees were preserved; all changes used isolated worktrees.

## 2026-08-28 — AllTrue student course summary slice live verification

- AllTrue issue [#2007](https://github.com/jerry200176-png/AllTrue_System/issues/2007) now has a bounded first slice: active student courses use task-first summary cards with explicit session progress, honest monthly/missing-session states, one primary action, and keyboard-accessible secondary actions. Existing API payloads, mutation handlers, permissions, billing, attendance, scheduling, and history behavior were preserved.
- The implementation was merged through PR [#2157](https://github.com/jerry200176-png/AllTrue_System/pull/2157) as `84c9e2e6e7767627c8befb55af00d53514f3d08d`. Required GitHub checks passed, including Presubmit, Vite Frontend Build, UI Smoke (Playwright), security, docs, control-plane, and golden-scenario checks.
- Deploy run [33184486346](https://github.com/jerry200176-png/AllTrue_System/actions/runs/33184486346) passed. Production `version.json` reports build SHA `84c9e2e6e7767627c8befb55af00d53514f3d08d`; `/api/v1/health` returned `ok`.
- Post-deploy read-only Calendar/Course Acceptance run [33184796064](https://github.com/jerry200176-png/AllTrue_System/actions/runs/33184796064) reached the calendar page and completed its API parity reads, but failed on the stale `.smart-cal-title` UI selector before course-page assertions. Production remained healthy; this acceptance contract follow-up is still open.
- TeacherHome priority-rule clarification was merged as PR [#2158](https://github.com/jerry200176-png/AllTrue_System/pull/2158), SHA `1a43a4ad0303458abacd71f5c0e04325f911f500`; main CI [33186834949](https://github.com/jerry200176-png/AllTrue_System/actions/runs/33186834949), deploy [33186993773](https://github.com/jerry200176-png/AllTrue_System/actions/runs/33186993773), production version, and health all passed. A second acceptance run [33187279382](https://github.com/jerry200176-png/AllTrue_System/actions/runs/33187279382) reproduced the same stale selector failure, so the parity gate remains open.
- This is a first course-summary slice, not completion of #2007's broader course-management IA cleanup. AllTrue remains at 70 open issues and five open PRs; cross-repo totals remain 76 open issues and 16 open PRs.
- Exo's merge audit required an explicit break-glass record because stale session metadata produced a false ungoverned/drift result; the override reason, green required checks, and normal squash merge are recorded in the product session audit. No admin or force operation was used.

## 2026-08-28 — AllTrue UI slices live verification

- AllTrue PR [#2154](https://github.com/jerry200176-png/AllTrue_System/pull/2154) was squash-merged as `2e1d0cd28ae936f74285dbbea835244779c6aa7c` after all required PR checks passed.
- CI deploy run [33166606478](https://github.com/jerry200176-png/AllTrue_System/actions/runs/33166606478) passed. Production `version.json`, Pi HEAD, deployment manifest, health, API smoke, and authenticated director UI smoke all matched the merge SHA; the director UI smoke passed at 390, 412, 768, 1280, and 1440px.
- Issue [#911](https://github.com/jerry200176-png/AllTrue_System/issues/911) is now closed as completed by the bounded daily-progress implementation. AllTrue currently has 70 open issues and 5 open PRs; current cross-repo totals are 76 open issues and 16 open PRs.
- The follow-up sidebar-focus slice, PR [#2155](https://github.com/jerry200176-png/AllTrue_System/pull/2155), was merged as `c44ea6aff907d79f8ea80da56edd06619e899e32`. Deploy run [33167200741](https://github.com/jerry200176-png/AllTrue_System/actions/runs/33167200741) passed exact-SHA production deployment, health, read-only API smoke, bundle checks, and director endpoint probes; production `version.json` and Pi HEAD match `c44ea6af`.
- Portfolio triage is refreshed in [`reports/2026-08-28/github-triage.md`](reports/2026-08-28/github-triage.md); portfolio-ops PR [#50](https://github.com/jerry200176-png/portfolio-ops/pull/50) has all five remote checks passing and remains ready for a separate merge session.

> These are two bounded UX slices, not a claim that every open issue/PR is resolved. The UX slice deployment is verified, while the post-deploy acceptance selector follow-up and #2007, #2002, #2129, and the remaining queues stay separately tracked.

## 2026-08-28 — GitHub portfolio and AllTrue UI V1 (pre-release snapshot)

- Fresh GitHub read-back covers six owner-visible repositories: 79 open issues
  and 15 open PRs. AllTrue has 73 open issues (33 P1-labelled) and five open
  PRs; Sunrise has four issues (three P1-labelled) and three open PRs; the
  remaining repositories are listed in
  [`reports/2026-08-28/github-triage.md`](reports/2026-08-28/github-triage.md).
- The main UI signal is AllTrue PR [#2129](https://github.com/jerry200176-png/AllTrue_System/pull/2129): it is not a release candidate because its 1,279-line diff fails the PR-size gate and UI Smoke. A bounded V1 was therefore implemented separately in isolated branch `chore/task-uiux-github-20260828`, linked to issue [#911](https://github.com/jerry200176-png/AllTrue_System/issues/911).
- The V1 adds `TodayProgressCard` to the director focus view. It uses only
  loaded `todaySchedules` and `attended` state, shows completed/total progress,
  separates loading from empty state, and routes the next action through the
  existing dashboard navigation. No API, permission, billing, schedule, or
  production data behavior changed.
- Read-only production checks passed: AllTrue health returned `ok` and serving
  SHA was `4a6b2a32`; Sunrise booking health returned `ok` and serving commit
  was `f8927b17`. These are observation evidence only; the V1 is not deployed.
- Existing dirty/diverged worktrees were preserved. Full workspace evidence is
  in [`reports/2026-08-28/workspace-inventory.md`](reports/2026-08-28/workspace-inventory.md).

### Current decisions required

1. Independent UI review and required checks for the new V1 Draft PR.
2. Keep the production-sensitive AllTrue #2086 release gate separate from the
   UI change; never bundle billing/attendance fixes with the UX slice.
3. After merge/deploy, verify serving SHA, health, and UI smoke before calling
   the UI improvement live.

> Current baseline: 2026-08-27. The historical entries below are retained as an audit trail; the current priority and execution state are defined by this section and `state/work-queue.yaml`.

## 2026-08-27 — AllTrue director workflow reliability and release gate

- AllTrue remains Tier 0 and live. Read-only production evidence: version
  `5e6598052299386bbf13e12ae320b90186022348` (built 2026-08-26 17:18 UTC);
  health is `ok`.
- The Xindian director's report about the eighth lesson for 周芮緗 was
  reproduced at the application boundary. A stale manual-booking response
  could let an earlier HTTP 422 overwrite the newer valid 8/29 check; this
  was a workflow defect, not merely a data correction.
- AllTrue PR [#2086](https://github.com/jerry200176-png/AllTrue_System/pull/2086)
  contains the latest-only response guard, correct next-session date
  selection, retryable conflict UI, and a real Vue page-level Playwright
  regression for the delayed-422 race. Its latest head `cfc5a1f6` also cancels
  superseded requests; local 304/304 unit tests, the targeted Playwright
  regression, and remote CI run `33035364530` pass. The PR is open with no
  independent review and is not deployed.
- AllTrue PR [#2085](https://github.com/jerry200176-png/AllTrue_System/pull/2085)
  adds a clear 44px mobile touch target for director dashboard actions. Local
  lint, 303/303 unit tests, and 120/120 UI Foundation cases pass; remote run
  33034901065 also passed. Independent review is still required.
- Dependabot currently reports three open `laravel/framework` advisories on
  the production backend (one high, two medium); the lockfile resolves
  `8.x-dev`. This is tracked as a separate security upgrade plan and must not
  be mixed into the attendance fix.
- No production attendance, billing, schedule, or account data was mutated
  by this work. The deployed version therefore remains the source of truth
  until the PR is independently reviewed, merged, deployed, and verified.
- A read-only `scripts/release-evidence.py` check is now available to compare
  the formal version/health endpoints against the expected commit; green CI
  alone is explicitly insufficient for release closure.
- The 10:53 +08:00 release-gate check returned health HTTP 200 but a SHA
  mismatch (`5e659805` serving versus PR #2086 `4af00816` expected), confirming
  that the fix is not deployed. Evidence: `reports/2026-08-27/alltrue-release-gate-2086.md`.
- Next tracked product risk: issue #2002, cross-date rescheduled sessions can
  occupy availability while being absent from the teacher calendar. A
  contract proposal and test matrix are recorded; implementation requires a
  separate high-risk review and Founder gate.

### Current execution order

1. Obtain independent review for AllTrue PR #2086, then merge/deploy only
   through the governed release path.
2. Run read-only release evidence against the deployed SHA and perform
   authenticated director acceptance for the 8/29 eighth-session workflow.
3. Design and review the cross-date calendar/availability consistency fix
   for AllTrue #2002; do not auto-materialize ambiguous schedule records.
4. Continue the remaining Portfolio freshness and governance checks; stale
   production evidence blocks closure.

Last updated: 2026-08-27. PR #2086 is a release candidate, not a production
completion claim.

> Historical baseline: 2026-08-01. This entry is retained as an audit trail; the current priority and execution state are defined by the 2026-08-27 section above and `state/work-queue.yaml`.

## 2026-08-01 — Platform optimization baseline and execution reset

- Both products remain Tier 0 and live.
- AllTrue canonical `main` was clean but stale locally; implementation now uses an isolated worktree from current `origin/main` (`01a34ae2`). The user's existing checkout was not reset or edited.
- Sunrise's existing dirty `chore/dependabot-major-policy` checkout was not touched. Its current bounded work is #211 code-side hardening, #257 single deploy ownership, and #261 typecheck baseline.
- AllTrue #1408 was stale: #1402, #1409, and #1410 are merged. The board is being reconciled before new work is opened.
- Founder-only gates remain explicit: AllTrue #1401 privacy review, #1387 credential rotation, Sunrise production migrations/paid infrastructure, merges, and deploys.
- New control matrix: `docs/incident-control-matrix.md`. New evidence report: `reports/2026-08-01/platform-optimization-baseline.md`.
- Portfolio control-plane PR #27 is merged; AllTrue #1428 ([#1579](https://github.com/jerry200176-png/AllTrue_System/pull/1579)), AllTrue #1420 ([#1580](https://github.com/jerry200176-png/AllTrue_System/pull/1580)), and Sunrise #261 ([#267](https://github.com/jerry200176-png/sunrise-cafe/pull/267)) are merged and live-verified.

### Live release evidence

- AllTrue #1428 PR [#1579](https://github.com/jerry200176-png/AllTrue_System/pull/1579) is merged. Deploy run [30685428337](https://github.com/jerry200176-png/AllTrue_System/actions/runs/30685428337) passed; production `deployment.json` backend SHA was `0fef175a`, health was `ok`, and smoke passed.
- AllTrue #1420 PR [#1580](https://github.com/jerry200176-png/AllTrue_System/pull/1580) is merged. Deploy run [30685651049](https://github.com/jerry200176-png/AllTrue_System/actions/runs/30685651049) passed database backup, the `security_audit_events` migration, SHA/health checks, and post-merge smoke; production backend SHA is `510f6b2e`.
- Sunrise #261 PR [#267](https://github.com/jerry200176-png/sunrise-cafe/pull/267) is merged. Deploy run [30685328910](https://github.com/jerry200176-png/sunrise-cafe/actions/runs/30685328910) and read-only verify run [30685328925](https://github.com/jerry200176-png/sunrise-cafe/actions/runs/30685328925) passed for `6605204e`; `/api/version` matches and `/api/booking-health` is `ok`.
- Existing Sunrise `rate_limit_mode=memory`, `rate_limit_grade=degraded_per_isolate`, and `stripe_enabled=false` remain tracked under #211; they were not silently changed by this release.

### Current execution order

1. Preserve live evidence and update the queue after every production release; never infer runtime state from a green PR alone.
2. Sunrise #257 live ownership verification (read-only Founder/dashboard evidence; code contract is already on main).
3. Sunrise #211 RLS/rate-limit/backup execution, with production migration and paid-plan Founder gates.
4. Architecture and UX slices after reliability evidence is green.

Last updated: 2026-08-01 (#1387 remains Founder-triggered; #1401 remains
Founder-reviewed; AllTrue #1428/#1420 and Sunrise #261 now have Draft PR evidence.
See the current baseline section above.)

## 2026-07-26 — #1387 confirmed match + rotation prepared; #1401 impact audit run

**#1387 — highest-priority open item.** The fingerprint audit (triggered
from `main` after PR #1421 merged) returned **`MATCH_ROTATION_REQUIRED`**
for `DB_PASSWORD`: the pre-fix leaked value is still the live production
database password. Every preparatory/verification step this session can
do without touching production is now done and merged to `main`:

- Every credential consumer identified (the Laravel app + every CI
  workflow reading `.env` fresh at SSH-run time — no hardcoded secondary
  copy exists anywhere).
- Backup/rollback readiness re-verified with **fresh** evidence (run
  `30178339123`, today's 6h backup restored cleanly, core tables
  plausible, test DB cleaned up) — not 3.5-week-old evidence.
- A rollback-safe rotation workflow (`1387-db-password-rotation.yml`,
  PR #1424, **merged**) that generates the new password entirely inside
  one remote SSH session (never printed/logged anywhere), applies it via
  `ALTER USER` + `.env`, verifies with `mysqladmin ping`, rebuilds config
  cache, and polls health before declaring success. Dormant until
  triggered — requires a typed `confirm=ROTATE` input.
- Minimal Founder runbook (`docs/incidents/1387-rotation-runbook.md`):
  the Founder never types a credential, only runs one `gh workflow run`
  command.

**This session did not trigger it.** Per this repo's own
`OPERATIONS_RUNBOOK.md` §O.2 (DB password rotation requires explicit
user approval at execution time) and given this is the first live-fire
run of a brand-new script against the only production instance of a live
system, the trigger itself is reserved as the one Founder action.

**#1401 — technical containment fully complete.** Production deploy of
PR #1400 independently confirmed via git ancestry (not just self-reported
in the issue). Adjacent-endpoint audit found no unfixed instance of the
pattern. Regression coverage merged and re-confirmed on `main` (56
tests/195 assertions green). The privacy impact audit was designed,
merged, and **run once** from `main`: 175 unverified/legacy bindings, 2
LINE identities spanning multiple families among all-time bindings (0
among currently-verified) — classified `insufficient-logs`, not
`confirmed-impact` or `no-evidence-found`, since the 2 flagged identities
have an equally plausible benign explanation only a human with production
access can resolve. A private, no-PII manual-review checklist (PR #1425)
gives that human the exact query and decision tree to do so.

**No family notified, no #1401 closure, no regulatory report — all still
open, human-only decisions**, per standing instruction.

## 2026-07-25 — Claude Code instructions-architecture audit (portfolio-ops itself)

Three-phase audit of this repo's own instruction architecture (CLAUDE.md,
`.claude/rules/`, Skills, Subagents, Hooks/Permissions, auto memory),
grounded in current official Claude Code docs fetched live this session —
merged as [PR #6](https://github.com/jerry200176-png/portfolio-ops/pull/6)
(commit `2492bed`, merge commit `d4ebc66`). Founder-approved after
re-verifying head commit, file scope, secret scan, and regression tests
immediately before merge.

- CLAUDE.md was already under the official 200-line guidance and correctly
  scoped — not blindly shortened; grew +4 lines to close a real gap (no
  rule previously existed stating safety policy/production boundaries/Git
  destructive-operation controls must never move to auto memory).
- Added `.claude/rules/` (didn't exist before): path-scoped conventions for
  agent definitions and portfolio-state YAML schema — zero fixed context
  cost, load only on matching files.
- Added `permissions.deny` to `.claude/settings.json` (6 literal
  destructive-command patterns) as a defense-in-depth layer alongside the
  existing `guard_bash.py`/`deny_tool.py` hooks, per official guidance that
  hook-based Bash pattern-matching is best-effort/fail-open — hooks
  unchanged, nothing replaced.
- Collapsed a 3-way redundant restatement of the Never-list (CLAUDE.md,
  `AUTONOMY_POLICY.md`, `COMPANY_CONSTITUTION.md`) to one authoritative
  source + one always-on summary + one pointer; trimmed a duplicated
  procedure block in `docs/operating-model.md`; fixed two dead file
  references.
- Verified before merge: hook regression suite green (18 safe + 38
  dangerous), `settings.json` valid JSON, all 7 read-only agents still
  lack `Write`/only `repo-maintainer` has it, `/portfolio-maintain status`
  resolves end-to-end, full diff secret-scanned clean, no product repo /
  incident evidence / autonomy / merge / deploy / agent-write boundary
  touched.

**Portfolio OS optimization work stops here for this session** — no
further Star-cleanup, reference-schema, or provenance-redesign follow-up
unless a real defect surfaces. Next: AllTrue #1401 containment (single
Tier-0 item), in `AllTrue_System` only.

## 2026-07-25 round 2 — AllTrue #1387 containment, Portfolio OS merge, priority reorder

- **AllTrue #1387: 4 of 5 Founder closure conditions now met.** Repo
  private ✅, replacement verified ✅ (CI-side), Actions-log exposure
  removed ✅ (run `30086225720` logs deleted, verified 404; artifacts
  precisely checked — clean, untouched), evidence documented ✅. The one
  remaining blocker — confirming the leaked DB password was never real/
  reused in production — has its verification tool built and tested
  (AllTrue_System PR [#1414](https://github.com/jerry200176-png/AllTrue_System/pull/1414),
  Draft, not merged) but **cannot run yet**: GitHub requires
  `workflow_dispatch` workflows to exist on the default branch before
  they're triggerable, which requires either merging #1414 (outside this
  session's product-repo merge authority) or a direct push to `main`
  (forbidden). **Recommendation revised to NOT READY TO CLOSE** — Founder
  merging #1414 and running it is the single remaining action.
- **GitHub personal Security log**: no programmatic access exists (3
  endpoint shapes tried, all 404) — this is an Enterprise/org-only API
  surface. Founder must check `github.com/settings/security-log` directly
  if the visibility-change root cause matters.
- **Portfolio OS PR #1**: merged (commit `3f325cbd`) after fixing a second
  hook false-positive (descriptive text in PR bodies/commit messages was
  being denied as if it were a real command — fixed narrowly, regression-
  tested both directions, live-proved in a throwaway repo) and a clean
  full-diff secret scan. Local `main` fast-forwarded, working tree clean.
- **Priority reorder** (AllTrue #1401 vs. Sunrise Vercel cap vs. Sunrise
  Agent Session Provenance CI): #1401 remains the single highest-severity
  item (PII of minors) but its remaining work is Founder-only (legal/
  notification), not something `execute` mode (Draft-PR engineering work)
  can act on. Comparing the other two on actual user/production impact and
  ongoing recurrence: the Vercel deployment cap is recurring across
  multiple dates and hits **production** directly (blocking releases,
  including future fixes), while the Provenance CI failures — though also
  recurring — have no end-user impact, only an internal governance gate.
  **Selected for `execute`: Sunrise Vercel deployment-capacity cap.**
  Caveat found during selection: this project is on Vercel's Hobby (free)
  tier and has already iterated on code-side mitigations (`ignoreCommand`,
  cron-frequency reductions in PRs #203/#206) — the durable fix may turn
  out to be a Founder billing decision (plan upgrade) rather than pure
  code, but a further code-side reduction in build/deploy volume hasn't
  been fully explored yet and is this session's next concrete step if
  continued.

## Executive Summary

- Active projects: 2 (AllTrue System, Sunrise Cafe), both Tier 0, both live
  in production.
- **Portfolio-level highest risk (revised this pass): AllTrue issue #1401**
  — a parent-portal cross-student PII exposure affecting minors' data. The
  code fix (PR #1400) is merged, but the production deploy is
  self-reported/unverified and the incident's own containment checklist
  (parent notification, evidence retention, exposure-log review) is
  entirely unexecuted. This outranks SEC-ALLTRUE-003 (below) because it is
  an *active* authorization-boundary bug, not a now-contained historical
  exposure.
- **AllTrue repo visibility — RESOLVED this pass, with explicit Founder
  approval given live in this session.** `AllTrue_System` is now private
  (changed via `gh api`, independently re-verified with a fresh read: 0
  forks, 0 releases, Pages disabled — no other public surface found). The
  one remaining blocker to closing issue #1387 is credential-reuse
  verification (was the exposed DB password ever real/used outside
  ephemeral CI) — this session has no tool access to DB/provider audit
  logs to confirm that either way. Full exposure inventory, unauthorized-
  use assessment, and history-cleanup impact analysis:
  `reports/2026-07-25/alltrue-sec-1387-incident-status-card.md` §16–19.
- **New candidate P0**: a GitGuardian 3-secret cluster (Telegram Bot Token,
  Laravel APP_KEY, Bearer Token) flagged 2026-07-17. Not yet confirmed
  whether this duplicates the already-rotated SEC-ALLTRUE-001 set or is a
  new exposure — pending direct secret-scanning confirmation.
- **Sunrise is no longer stale** — fresh triage completed this pass. Two
  findings escalate Sunrise's risk: (1) the Vercel deployment-capacity cap
  now confirmed hitting **production** deploys directly, not just preview;
  (2) issue #211's Founder decisions (FD-1…FD-6: RLS, rate limiting, backup
  posture) were made 2026-07-19 but **zero execution PRs exist since** —
  fail-open rate limiting is confirmed live in production right now.
- Also new: Sunrise's "Agent Session Provenance" CI check is failing
  repeatedly (8x/30 days per Gmail, confirmed as a real failing required
  check on PR #253 via GitHub) — needs log-level triage to classify as a
  CI bug or a genuine policy violation.
- **Portfolio OS**: created private repo `jerry200176-png/portfolio-ops`
  (Founder-approved), pushed `main` and `chore/portfolio-maintenance-os`,
  opened Draft PR [#1](https://github.com/jerry200176-png/portfolio-ops/pull/1)
  — not merged. Along the way, a real hook false-positive was found and
  worked around without weakening the hook: `guard_bash.py` blocked a `gh
  pr create` call because the PR body's own *description* of the hook's
  blocking rules contained the literal substring "git reset --hard" —
  fixed by rephrasing the text, not by touching the hook. Hook live-
  blocking was separately proven in a disposable throwaway repo this
  session (created and destroyed within scratchpad only).
- This pass made two irreversible-adjacent changes (repo visibility,
  new-repo creation/push/PR) **only after explicit Founder approval given
  live in this conversation** — an earlier "stop hook feedback" message
  that asserted approval had already been granted was treated as untrusted
  and not acted on until the Founder confirmed directly. No merges, no
  deploys, no production-data changes, no issue closures were performed.

## Tier 0 priority ordering (this pass)

1. **AllTrue #1401** — active cross-student PII exposure, containment
   unexecuted. Stop-the-line.
2. **Sunrise OPS-SUNRISE-001** — Vercel cap now hitting production.
3. **Sunrise SEC-SUNRISE-002** — decided-but-unexecuted RLS/rate-limit/
   backup work; fail-open rate limiting live now.
4. **AllTrue GitGuardian cluster** — candidate P0, pending dedup
   confirmation against SEC-ALLTRUE-001.
5. **AllTrue SEC-ALLTRUE-003** — visibility RESOLVED this pass; only
   credential-reuse verification remains, treated as lower urgency now
   that public exposure is closed.
6. **Sunrise Agent Session Provenance CI failures** — governance gate,
   needs log triage to determine severity.

## Portfolio Table

| Tier | Product | Production | Git status | CI | Critical work | UX risk | Current action | Next action | Data freshness |
|---|---|---|---|---|---|---|---|---|---|
| 0 | AllTrue System | live, health OK, version `8b4a30f1` (2 commits behind main, normal deploy lag) | main clean, 101 commits behind origin/main locally (not touched) | PR #1400, #1395 merged; PR #1333 confirmed merged (was misreported as "validating_ci") | #1401 containment unexecuted (P0); repo visibility unresolved (P0); GitGuardian cluster pending confirmation (P0); #1096 billing bug, #1100 package-overlap decision (P1) | not assessed this pass | Founder decision on #1401 containment + repo visibility | see Decisions Required | **Fresh — 2026-07-25 14:30, this triage** |
| 0 | Sunrise Cafe | live, health OK; deployed commit confirmed current `origin/main` HEAD (not behind despite stale local checkout) | `chore/dependabot-major-policy` branch, dirty (uncommitted wildcard change, not touched), 7 commits behind origin/main | main CI green; PR #253 failing Agent Session Provenance check | Vercel cap hitting production (P0, escalated); #211 decided-not-executed (P0); provenance CI failures (P1) | medium | none taken this pass | see Decisions Required | **Fresh — 2026-07-25 14:30, this triage** |

## Work Completed (this session)

- AllTrue: GitHub triage and Gmail signal analysis re-run and consolidated.
  Corrected `PROD-ALLTRUE-003` from stale "validating_ci" to confirmed
  merged. Surfaced #1401 (new top P0) and the GitGuardian cluster
  (candidate P0, pending confirmation). Added #1096 and #1100 as tracked
  P1 items.
  **With explicit Founder approval given live in this session**: changed
  `AllTrue_System` from public to private, re-verified, confirmed no other
  public surface (0 forks/releases, Pages disabled). Completed a full
  exposure inventory (branches/tags/code-search/Actions artifacts),
  unauthorized-use assessment (confirmed evidence vs. absence-of-evidence
  vs. unavailable evidence, explicitly), and a history-cleanup impact
  assessment (documented, no rewrite performed). Proposed — but did not
  execute — an Actions-log deletion candidate for run `30086225720`. Full
  detail: `reports/2026-07-25/alltrue-sec-1387-incident-status-card.md`
  §16–19. Recommendation on issue #1387 revised to **READY TO CLOSE WITH
  EXPLICIT RESIDUAL RISK** (credential-reuse verification still open) —
  this session did not close the issue.
- Sunrise: full fresh triage completed (previously 6 days stale). Escalated
  the Vercel capacity issue from "preview-only" to "confirmed hitting
  production." Reclassified #211/SEC-SUNRISE-002 from "queued" to
  "decided_not_executed" to reflect that Founder decisions exist but
  nothing has shipped. Added the Agent Session Provenance CI failure
  pattern as a new tracked item. Local uncommitted `dependabot.yml` change
  on `chore/dependabot-major-policy` confirmed structurally identical to
  what's already live on `origin/main` (merged PR #249) — left untouched
  pending Founder/orchestrator confirmation of branch intent.
- Portfolio OS: **with explicit Founder approval given live in this
  session**, created private repo `jerry200176-png/portfolio-ops`, pushed
  `main` and `chore/portfolio-maintenance-os`, opened Draft PR
  [#1](https://github.com/jerry200176-png/portfolio-ops/pull/1) covering
  architecture, skill/agent/hook design, tests, threat model, rollback,
  and known limitations. Not merged. Diff was reviewed for secret patterns
  before pushing (none found — only type-name references in evidence
  text).
- Hook robustness: found and worked around (without weakening) a
  `guard_bash.py` false positive — a PR-body *description* of the hook's
  own blocking rules literally containing "git reset --hard" was flagged
  as if it were a real command. Confirmed live hook-blocking separately in
  a disposable throwaway repo (created/destroyed in scratchpad only).
- `state/work-queue.yaml` and `portfolio.yaml` updated with all findings
  above; see `reports/2026-07-25/github-triage.md` and
  `reports/2026-07-25/gmail-signals.md` for full evidence and score
  rationale.

## Decisions Required

1. **AllTrue #1401 containment** (most urgent) — confirm production
   deploy of PR #1400 and execute the incident's containment checklist
   (parent notification, evidence retention, exposure-log review). PII of
   minors, legal-adjacent — this session does not act unilaterally.
2. ~~AllTrue repository visibility~~ — **RESOLVED this pass** (private,
   re-verified, no other public surface found).
3. **AllTrue credential-reuse verification** (now the sole blocker on
   SEC-ALLTRUE-003) — confirm the pre-fix DB password was never used as a
   real credential outside ephemeral CI; rotate anywhere it was. No tool
   in this session can check DB/provider audit logs — needs Founder or an
   ops-side check.
4. **AllTrue Actions-log residual exposure** — decide whether to accept
   run `30086225720`'s log as residual risk or delete it (proposed
   deletion list in the incident card §17; nothing deleted).
5. **Issue #1387 closure** — this session's recommendation is READY TO
   CLOSE WITH EXPLICIT RESIDUAL RISK (if Decision 3's risk is accepted) or
   NOT READY TO CLOSE (if certainty is required); final call and the close
   action itself are the Founder's.
6. **AllTrue GitGuardian 3-secret cluster** — confirm whether the
   2026-07-17 alerts (Telegram, APP_KEY, Bearer) duplicate the
   already-rotated SEC-ALLTRUE-001 set or represent a new exposure.
7. **Sunrise Vercel production-deployment cap** (escalated) — confirm
   current capacity status directly via Vercel dashboard/API (not yet done
   this pass); decide whether to open a dedicated GitHub issue since #211
   does not cover this.
8. **Sunrise #211 execution** — decide whether to greenlight execution of
   the already-made FD-1…FD-6 decisions (RLS, rate limiting, backup
   posture) as the next `execute`-mode work, given fail-open rate limiting
   is confirmed live in production now.
9. **Sunrise `chore/dependabot-major-policy` branch** — confirm whether
   this branch (uncommitted wildcard dependabot change, content already
   matches merged PR #249) is stale/redundant or represents in-progress
   intent that should continue.
10. ~~portfolio-ops remote~~ — **RESOLVED this pass**: private repo
    created, branches pushed, Draft PR #1 open.
11. **portfolio-ops Draft PR #1** — review and decide when/whether to
    merge (this session will not merge it).

## Next Highest-ROI Actions (max 5, portfolio-wide)

1. Founder confirms AllTrue #1401 production deploy and executes the
   containment checklist — highest-stakes, PII-of-minors, currently
   entirely unactioned.
2. Founder (or an ops-side check) confirms AllTrue DB-password non-reuse
   (Decision 3) — the single remaining blocker to closing #1387 cleanly —
   and decides on the Actions-log residual risk (Decision 4).
3. Direct Vercel dashboard/API check for Sunrise capacity status, followed
   by a Founder go-ahead to execute Sunrise #211's already-decided items
   (RLS, rate limiting, backup posture) via `execute` mode.
4. Log-level triage of Sunrise's Agent Session Provenance CI failures on
   PR #253 to classify as CI bug vs. real policy violation, and resolve
   the GitGuardian dedup question (Decision 6).
5. Review portfolio-ops Draft PR #1 and decide on the
   `chore/dependabot-major-policy` branch — both low-effort administrative
   items now that the higher-stakes containment work is done.
