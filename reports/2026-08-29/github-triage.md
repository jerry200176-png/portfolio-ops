# GitHub portfolio triage — 2026-08-29

Capture time: 2026-08-29 07:52 +08:00. GitHub API/`gh` read-back is the
source of truth for issue and pull-request state. Existing dirty or diverged
checkouts were preserved; the workspace inventory is recorded in
[`workspace-inventory.tsv`](workspace-inventory.tsv).

## Current owner-visible counts

| Repository | Open issues | Open PRs | Current open PR register |
|---|---:|---:|---|
| [AllTrue System](https://github.com/jerry200176-png/AllTrue_System) | 70 | 5 | #2129, #2112, #2092 draft, #2021, #1991 draft |
| [Portfolio Ops](https://github.com/jerry200176-png/portfolio-ops) | 2 | 6 | #47, #42, #40 draft, #39 draft, #36, #35 |
| [Engineering Intelligence](https://github.com/jerry200176-png/engineering-intelligence) | 0 | 1 | #1 |
| [Sunrise Cafe](https://github.com/jerry200176-png/sunrise-cafe) | 4 | 3 | #299, #298, #297 |
| [Income Statement App](https://github.com/jerry200176-png/income-statement-app) | 0 | 0 | none |
| [Income Statement App Releases](https://github.com/jerry200176-png/income-statement-app-releases) | 0 | 0 | none |
| **Total** | **76** | **15** | |

The five AllTrue PRs are existing open work and were not merged as part of
this UX release. The old TeachersList #693 and Attendance #695 rollout
issues are now marked CLOSED/COMPLETED by GitHub; the active broad UX epic is
[#1600](https://github.com/jerry200176-png/AllTrue_System/issues/1600).

## AllTrue release evidence

- [PR #2174](https://github.com/jerry200176-png/AllTrue_System/pull/2174)
  shipped the bounded TeacherHome daily-queue trust slice and was squash-merged
  as `95a7f7d79b479549284ace4a72c43db36a447212`. The queue now waits for core
  attendance, learning, overdue, schedule, and parent-reply sources; failed or
  incomplete data is shown as `待確認` with an accessible alert and retry action,
  never as an all-clear state.
- Local TeacherHome accessibility passed 3/3 and real Vue page E2E passed 5/5;
  the documented production build, lint, design/fixture gates, and `exo check`
  passed. Main CI
  [33221362938](https://github.com/jerry200176-png/AllTrue_System/actions/runs/33221362938),
  control-plane enforce
  [33221362903](https://github.com/jerry200176-png/AllTrue_System/actions/runs/33221362903),
  Deploy to Pi
  [33221455473](https://github.com/jerry200176-png/AllTrue_System/actions/runs/33221455473),
  read-only production acceptance
  [33221646376](https://github.com/jerry200176-png/AllTrue_System/actions/runs/33221646376),
  and Pi Health
  [33221727676](https://github.com/jerry200176-png/AllTrue_System/actions/runs/33221727676)
  passed.
- Production identity read-back is GREEN: remote main, backend, frontend build,
  and deployment manifest all match the merge SHA; health is HTTP 200/status
  `ok` with no drift. Evidence is recorded on
  [AllTrue #1618](https://github.com/jerry200176-png/AllTrue_System/issues/1618#issuecomment-5458952298).
- This is a bounded slice only; #1618 and broad #1600 remain open for further
  authenticated visual review and workflow work.

- [PR #2173](https://github.com/jerry200176-png/AllTrue_System/pull/2173)
  shipped the bounded navigation-shell More-surface slice and was
  squash-merged as `70323793f17a5caca1d3bb6d7ed6047fe8066e94`. Desktop More is
  a predictable non-modal panel; mobile More is a labelled modal sheet. Both
  support explicit dismissal and focus return while preserving role-scoped
  destinations, badges, permissions, and business handlers.
- Targeted navigation contracts passed 10/10; `lint:no-undef`, production
  build, design lint, `exo check`, PR UI Smoke, and Vite Frontend Build passed.
  Full `vitest run` remains a non-signal in this repository because its glob
  mixes Node-style test files and Playwright specs with Vitest suites; the
  documented build command passed.
- Deploy [33220048573](https://github.com/jerry200176-png/AllTrue_System/actions/runs/33220048573),
  read-only production acceptance
  [33220266993](https://github.com/jerry200176-png/AllTrue_System/actions/runs/33220266993),
  and Pi Health [33220353183](https://github.com/jerry200176-png/AllTrue_System/actions/runs/33220353183)
  passed. Production identity read-back is GREEN with main, deployment
  manifest, frontend build SHA, and backend SHA aligned to the merge SHA; health
  is HTTP 200/status `ok`.
- Evidence is recorded on
  [AllTrue #1600](https://github.com/jerry200176-png/AllTrue_System/issues/1600#issuecomment-5458802888).

- [PR #2172](https://github.com/jerry200176-png/AllTrue_System/pull/2172)
  shipped the bounded NotificationsCenter workspace-semantics slice and was
  squash-merged as `08fba2c0874da160d8ab1b8c71709788c68e5b4f`.
- The主任收件匣 tabs now expose stable tab-to-panel relationships; tuition report
  uses shared AtDialog semantics for initial focus, Escape, close, and scroll
  locking; notification action buttons explicitly stay out of form submission.
  Payment, reconciliation, receipt, notification data, API, permission, and
  navigation behavior were unchanged.
- Main CI [33218067240](https://github.com/jerry200176-png/AllTrue_System/actions/runs/33218067240),
  Deploy to Pi [33218300044](https://github.com/jerry200176-png/AllTrue_System/actions/runs/33218300044),
  Pi Health [33218547562](https://github.com/jerry200176-png/AllTrue_System/actions/runs/33218547562),
  and read-only production acceptance
  [33218527188](https://github.com/jerry200176-png/AllTrue_System/actions/runs/33218527188)
  passed. Release tag `v2026.08.29.11` was created from the same merge SHA.
- Evidence is recorded on
  [AllTrue #1600](https://github.com/jerry200176-png/AllTrue_System/issues/1600#issuecomment-5458607891).

- [PR #2171](https://github.com/jerry200176-png/AllTrue_System/pull/2171)
  shipped the bounded TeacherHome control-semantics slice and was squash-merged
  as `a637338026ab71e2a5d91ca5361ab388386829cd`.
- The clock-in status card is now a native labelled button; weekly navigation
  and schedule assessment/report icon controls expose explicit button types and
  accessible names. Attendance, schedule, assessment data truth, APIs,
  permissions, and navigation handlers were not changed.
- [Main CI 33215612471](https://github.com/jerry200176-png/AllTrue_System/actions/runs/33215612471),
  [Deploy to Pi 33215875727](https://github.com/jerry200176-png/AllTrue_System/actions/runs/33215875727),
  and [read-only production acceptance 33216138420](https://github.com/jerry200176-png/AllTrue_System/actions/runs/33216138420)
  passed. Local TeacherHome E2E passed 5/5 and full Vitest passed 74 files /
  343 tests.
- Production read-back returned HTTP 200 for
  [`/api/v1/health`](https://daan.lifenet.com.tw/api/v1/health),
  [`/version.json`](https://daan.lifenet.com.tw/version.json), and
  [`/deployment.json`](https://daan.lifenet.com.tw/deployment.json); all
  backend/frontend/build SHA values matched the merge commit.
- Release evidence is recorded on
  [AllTrue issue #1618](https://github.com/jerry200176-png/AllTrue_System/issues/1618#issuecomment-5458347820).
- Issue #1618 was re-opened intentionally after the bounded PR merged; its
  broader teacher daily workflow and authenticated visual review remain open.
  The lifecycle correction is recorded in the
  [reopen note](https://github.com/jerry200176-png/AllTrue_System/issues/1618#issuecomment-5458393226).

- [PR #2170](https://github.com/jerry200176-png/AllTrue_System/pull/2170)
  shipped the bounded Attendance workspace accessibility slice and was
  squash-merged as `67e3bba0e81bfcc6b1a7c2a39bb49574571f3df9`.
- The change connects director Attendance tabs to their selected panels,
  gives panels keyboard focus, exposes pending status choices as pressed
  buttons, and adds release-note/test coverage. Attendance APIs, records,
  deduction, RFID, permissions, and submit behavior were not changed.
- [main CI 33213233077](https://github.com/jerry200176-png/AllTrue_System/actions/runs/33213233077),
  [Deploy to Pi 33213514877](https://github.com/jerry200176-png/AllTrue_System/actions/runs/33213514877),
  and [read-only production acceptance 33213775735](https://github.com/jerry200176-png/AllTrue_System/actions/runs/33213775735)
  passed.
- Production read-back returned HTTP 200 for
  [`/api/v1/health`](https://daan.lifenet.com.tw/api/v1/health),
  [`/version.json`](https://daan.lifenet.com.tw/version.json), and
  [`/deployment.json`](https://daan.lifenet.com.tw/deployment.json). Health
  was `status=ok`; version and deployment backend/frontend SHA matched the
  merge commit.
- Release evidence is recorded on
  [AllTrue #1600](https://github.com/jerry200176-png/AllTrue_System/issues/1600#issuecomment-5458089013).

## Portfolio operating decision

1. Keep #1600 as the broad UX renewal epic; continue one deployable bounded
   slice per AllTrue release.
2. Continue #1618 with authenticated teacher workflow visual review and collect
   scan-to-first-action, tab-switch, keyboard/focus, and remaining state evidence
   before selecting the next slice.
3. Keep LearningRecords #1621 behind the #957/#1080 data-truth gate; do not
   merge the 1,279-line #2129/sidebar or other production-sensitive work as a
   side effect of this UI release.
4. Preserve the six-repository issue/PR inventory and current dirty-checkout
   warnings as evidence, rather than cleaning or resetting shared checkouts.
