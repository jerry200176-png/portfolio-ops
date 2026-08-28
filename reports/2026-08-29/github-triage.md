# GitHub portfolio triage — 2026-08-29

Capture time: 2026-08-29 06:24 +08:00. GitHub API/`gh` read-back is the
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
2. Collect Attendance scan-to-first-action, tab-switch, keyboard, and status
   misclassification evidence before selecting the next slice.
3. Keep LearningRecords #1621 behind the #957/#1080 data-truth gate; do not
   merge the 1,279-line #2129/sidebar or other production-sensitive work as a
   side effect of this UI release.
4. Preserve the six-repository issue/PR inventory and current dirty-checkout
   warnings as evidence, rather than cleaning or resetting shared checkouts.
