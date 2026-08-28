# GitHub portfolio triage — 2026-08-28

Capture time: 2026-08-29 02:03 +08:00. Source of truth for repository and
collaboration state: GitHub API/`gh` read-back in this session. Labels are
signals only; the shortlist below is cross-checked against PR checks, local
worktrees, and production read-only endpoints.

## 2026-08-29 refresh

- Fresh authenticated GitHub read-back covers six owner-visible repositories:
  76 open issues and 15 open PRs: AllTrue 70 issues / 5 PRs, Portfolio Ops 2 / 6, Engineering
  Intelligence 0 / 1, Sunrise Cafe 4 / 3, and both Income Statement repos 0 / 0.
- AllTrue PR [#2163](https://github.com/jerry200176-png/AllTrue_System/pull/2163)
  shipped the bounded teacher next-action slice for [#1618](https://github.com/jerry200176-png/AllTrue_System/issues/1618):
  the first existing task is now shown as `現在先做`, later work remains under
  `接著處理`, and existing task ordering, leave filtering, routing, permissions,
  and data behavior are unchanged. It merged as `31795f9b6a7be7523a4b4b69358cf1a61ba135c1`.
- Main CI [33196785637](https://github.com/jerry200176-png/AllTrue_System/actions/runs/33196785637),
  deploy [33196933804](https://github.com/jerry200176-png/AllTrue_System/actions/runs/33196933804),
  and read-only production acceptance
  [33197207380](https://github.com/jerry200176-png/AllTrue_System/actions/runs/33197207380)
  passed. Production version and health matched the merge SHA; issue #1618 remains open.
- AllTrue PR [#2159](https://github.com/jerry200176-png/AllTrue_System/pull/2159)
  repaired the calendar/course acceptance contract and merged as
  `96d2980aa8d93a88ea56fdb0b1ca8a5a980eca06`; its production acceptance run
  [33188606426](https://github.com/jerry200176-png/AllTrue_System/actions/runs/33188606426)
  passed both desktop and mobile parity checks.
- AllTrue PR [#2160](https://github.com/jerry200176-png/AllTrue_System/pull/2160)
  added the original learning-companion hero to TeacherHome and merged as
  `f29ad8a36f5dd5780a6c6b0d8baae85b322d99fb`. Local real-Vue evidence passed
  five normal/empty/error and responsive cases; main CI
  [33189424753](https://github.com/jerry200176-png/AllTrue_System/actions/runs/33189424753)
  and deploy [33189578837](https://github.com/jerry200176-png/AllTrue_System/actions/runs/33189578837)
  passed. Production `version.json` now reports `f29ad8a3` and health is ok.
- This refresh supersedes the earlier stale `.smart-cal-title` failure in runs
  [33184796064](https://github.com/jerry200176-png/AllTrue_System/actions/runs/33184796064)
  and [33187279382](https://github.com/jerry200176-png/AllTrue_System/actions/runs/33187279382);
  the selector remediation is now merged and the full acceptance run is green.
- AllTrue PR [#2161](https://github.com/jerry200176-png/AllTrue_System/pull/2161)
  merged a proposal-only student-course IA redesign for issue [#2007](https://github.com/jerry200176-png/AllTrue_System/issues/2007).
  It contains desktop/mobile wireframes, state rules, and implementation gates;
  #2007 remains open until product/director review and a later implementation
  release. The proposal comment is recorded at
  [the issue thread](https://github.com/jerry200176-png/AllTrue_System/issues/2007#issuecomment-5455191359).
- AllTrue PR [#2162](https://github.com/jerry200176-png/AllTrue_System/pull/2162)
  shipped Phase 2A of #2007: a course overview, attention-first active-course
  picker, focused detail card, and mobile scroll-preservation behavior. It
  merged as `a567f55e9a43d2214161347083a6e5d77067b5d6`; main CI
  [33194188998](https://github.com/jerry200176-png/AllTrue_System/actions/runs/33194188998),
  deploy [33194481228](https://github.com/jerry200176-png/AllTrue_System/actions/runs/33194481228),
  and read-only production acceptance
  [33194768520](https://github.com/jerry200176-png/AllTrue_System/actions/runs/33194768520)
  passed. Production version and health matched; #2007 was reopened after
  GitHub auto-closed it from the PR keyword because the parent issue remains
  the tracker for future IA phases.

## Portfolio snapshot

| Repository | Open issues | P1-labelled | Blocked-labelled | Open PRs | Immediate signal |
|---|---:|---:|---:|---:|---|
| [AllTrue System](https://github.com/jerry200176-png/AllTrue_System) | 70 | 33 | 37 | 5 | PR #2163 is merged/deployed for the teacher next-action slice; Calendar/Course acceptance is green |
| [Engineering Intelligence](https://github.com/jerry200176-png/engineering-intelligence) | 0 | 0 | 0 | 1 | PR #1 has failing checks and is the only open delivery item |
| [Portfolio Ops](https://github.com/jerry200176-png/portfolio-ops) | 2 | 0 | 0 | 6 | PR #52 merged the refreshed inventory; superseded PR #51 is closed; PR #40 remains draft/failing |
| [Sunrise Cafe](https://github.com/jerry200176-png/sunrise-cafe) | 4 | 3 | 0 | 3 | PR #298 fails checks; #257 remains the production ownership issue |
| [Income Statement App](https://github.com/jerry200176-png/income-statement-app) | 0 | 0 | 0 | 0 | No open GitHub work items |
| [Income Statement App Releases](https://github.com/jerry200176-png/income-statement-app-releases) | 0 | 0 | 0 | 0 | No open GitHub work items |

The six repositories above are the repositories returned by the authenticated
owner listing. The local workspace also contains `korea-trip-plan`, but its
remote currently returns “repository could not be resolved”; it is therefore
tracked as a local-only/unreachable remote, not silently treated as a healthy
GitHub project.

## Open PR register

| Repository | PR | State/check signal | Next action |
|---|---|---|---|
| AllTrue | [#2129](https://github.com/jerry200176-png/AllTrue_System/pull/2129) | Open; Presubmit and UI Smoke failed; Vite build passed | Split the 1,279-line UI change into reviewable slices and repair the course-management smoke contract before review; do not merge as-is |
| AllTrue | [#2112](https://github.com/jerry200176-png/AllTrue_System/pull/2112) | Open; failing check read back | Re-run/read the failing dependency check and merge only after required checks are green |
| AllTrue | [#2092](https://github.com/jerry200176-png/AllTrue_System/pull/2092) | Draft; no checks recorded | Decide whether the unused-variable ratchet is still needed, then make the PR reviewable or close it with evidence |
| AllTrue | [#2021](https://github.com/jerry200176-png/AllTrue_System/pull/2021) | Open; recorded checks have no failure | Obtain independent review and confirm it does not compete with the current production release gate |
| AllTrue | [#1991](https://github.com/jerry200176-png/AllTrue_System/pull/1991) | Draft; no checks recorded | Review RFC scope and either mark ready with evidence or close as stale |
| Engineering Intelligence | [#1](https://github.com/jerry200176-png/engineering-intelligence/pull/1) | Open; failing check read back | Inspect the failed real-LLM pipeline check before review |
| Portfolio Ops | [#47](https://github.com/jerry200176-png/portfolio-ops/pull/47) | Open; no failure recorded | Review Dependabot change |
| Portfolio Ops | [#42](https://github.com/jerry200176-png/portfolio-ops/pull/42) | Open; no failure recorded | Review governance documentation change |
| Portfolio Ops | [#40](https://github.com/jerry200176-png/portfolio-ops/pull/40) | Draft; failing check read back | Repair or close after checking current workspace manifest |
| Portfolio Ops | [#39](https://github.com/jerry200176-png/portfolio-ops/pull/39) | Draft; no failure recorded | Decide whether the research artifact is still current |
| Portfolio Ops | [#36](https://github.com/jerry200176-png/portfolio-ops/pull/36) | Open; no failure recorded | Review Dependabot change |
| Portfolio Ops | [#35](https://github.com/jerry200176-png/portfolio-ops/pull/35) | Open; no failure recorded | Review Dependabot change |
| Sunrise Cafe | [#299](https://github.com/jerry200176-png/sunrise-cafe/pull/299) | Open; no failure recorded | Review dev dependency group |
| Sunrise Cafe | [#298](https://github.com/jerry200176-png/sunrise-cafe/pull/298) | Open; failing check read back | Repair the production dependency group before review |
| Sunrise Cafe | [#297](https://github.com/jerry200176-png/sunrise-cafe/pull/297) | Open; no failure recorded | Review security pin and required production verification |

## Highest-value issue queues (maximum five per product)

### AllTrue

1. [#2002](https://github.com/jerry200176-png/AllTrue_System/issues/2002) —
   cross-date reschedule/calendar consistency; requires a reviewed projection
   contract before any materialization or data repair.
2. [#2129](https://github.com/jerry200176-png/AllTrue_System/pull/2129) —
   broad UI refactor; failed size/UI gates prove it is not a release candidate.
3. [#2007](https://github.com/jerry200176-png/AllTrue_System/issues/2007) —
   Phase 2A course overview and active-course selection is live through PR
   #2162; the broader course-management IA cleanup remains open and must stay
   presentation-only per slice.
4. [#1618](https://github.com/jerry200176-png/AllTrue_System/issues/1618) —
   teacher daily workflow; the first next-action slice is live, measure scan-to-first-action before the next slice.
5. [#2112](https://github.com/jerry200176-png/AllTrue_System/pull/2112) —
   Dependabot action update; keep dependency review separate from the UI work.

### Sunrise Cafe

1. [#257](https://github.com/jerry200176-png/sunrise-cafe/issues/257) —
   confirm single production deploy ownership through the read-only Founder
   dashboard check.
2. [#261](https://github.com/jerry200176-png/sunrise-cafe/issues/261) —
   typecheck baseline is represented by PR #267 in the historical queue; check
   whether the live issue should be closed with that evidence.
3. [#239](https://github.com/jerry200176-png/sunrise-cafe/issues/239) —
   phase-2 portfolio/product umbrella; split actionable children before work.
4. [#211](https://github.com/jerry200176-png/sunrise-cafe/issues/211) —
   RLS/rate-limit/backup and paid-plan decisions remain owner-gated.

Engineering Intelligence has no open issues; its only PR is the immediate
queue. Portfolio Ops has two open issues (#26 and #11); both are control-plane
maintenance items, not product release blockers.

## Read-only release and workspace evidence

- AllTrue PR [#2157](https://github.com/jerry200176-png/AllTrue_System/pull/2157)
  was squash-merged as `84c9e2e6e7767627c8befb55af00d53514f3d08d` after the
  required GitHub checks passed, including Vite Frontend Build and authenticated
  UI Smoke. Deploy run
  [33184486346](https://github.com/jerry200176-png/AllTrue_System/actions/runs/33184486346)
  passed; production `version.json` returned the same build SHA and
  `https://daan.lifenet.com.tw/api/v1/health` returned `{"status":"ok"}`.
  The slice changes active-course presentation only; issue #2007 remains open
  for the larger course-management IA work.
- AllTrue's post-#2157 read-only Calendar/Course Production Acceptance runs
  [33184796064](https://github.com/jerry200176-png/AllTrue_System/actions/runs/33184796064)
  and [33187279382](https://github.com/jerry200176-png/AllTrue_System/actions/runs/33187279382)
  reached both calendar viewports and completed the API parity reads, but
  failed before the course-page assertions because the test still required
  the removed `.smart-cal-title` class while production renders the same
  heading through `AtPageHeader`. The captured DOM showed the calendar heading,
  controls, and course cards; this is an acceptance-selector contract failure,
  not evidence of an API or deployment outage. The selector follow-up remains
  open and must pass before claiming the acceptance workflow green.
- The stale-selector statement above is historical and is superseded by PR
  [#2159](https://github.com/jerry200176-png/AllTrue_System/pull/2159): main CI
  [33188121141](https://github.com/jerry200176-png/AllTrue_System/actions/runs/33188121141),
  deploy [33188295787](https://github.com/jerry200176-png/AllTrue_System/actions/runs/33188295787),
  and the corrected production acceptance run
  [33188606426](https://github.com/jerry200176-png/AllTrue_System/actions/runs/33188606426)
  all passed. The read-only parity check completed calendar and course-page
  assertions at desktop and mobile widths.
- TeacherHome queue clarity PR [#2158](https://github.com/jerry200176-png/AllTrue_System/pull/2158)
  was squash-merged as `1a43a4ad0303458abacd71f5c0e04325f911f500`; main CI
  [33186834949](https://github.com/jerry200176-png/AllTrue_System/actions/runs/33186834949)
  and deploy [33186993773](https://github.com/jerry200176-png/AllTrue_System/actions/runs/33186993773)
  passed. Production `version.json` matched that SHA and health returned `ok`.
- TeacherHome visual companion PR [#2160](https://github.com/jerry200176-png/AllTrue_System/pull/2160)
  is the next presentation slice: an original generated learning companion,
  warm amber/navy surface, responsive layout, and real text/link semantics;
  it does not alter operational data or handlers. Main CI
  [33189424753](https://github.com/jerry200176-png/AllTrue_System/actions/runs/33189424753),
  deploy [33189578837](https://github.com/jerry200176-png/AllTrue_System/actions/runs/33189578837),
  and production read-back at 2026-08-29 00:25 all passed.
- AllTrue `https://daan.lifenet.com.tw/version.json` returned HTTP 200 with
  serving build SHA `a567f55e9a43d2214161347083a6e5d77067b5d6`, and
  `https://daan.lifenet.com.tw/api/v1/health` returned `{"status":"ok"}`.
- AllTrue PR [#2162](https://github.com/jerry200176-png/AllTrue_System/pull/2162)
  passed the local 124-case UI foundation suite and all required remote PR
  checks. Main CI run [33194188998](https://github.com/jerry200176-png/AllTrue_System/actions/runs/33194188998),
  deploy [33194481228](https://github.com/jerry200176-png/AllTrue_System/actions/runs/33194481228),
  and read-only acceptance [33194768520](https://github.com/jerry200176-png/AllTrue_System/actions/runs/33194768520)
  passed against the merged SHA; issue #2007 remains open for the next IA phase.
- AllTrue PR [#2154](https://github.com/jerry200176-png/AllTrue_System/pull/2154)
  closed issue [#911](https://github.com/jerry200176-png/AllTrue_System/issues/911)
  and deployed through run
  [33166606478](https://github.com/jerry200176-png/AllTrue_System/actions/runs/33166606478);
  production version, Pi HEAD, health, API smoke, and authenticated director UI
  smoke all matched the merge SHA. This is the post-release evidence for the
  bounded daily-progress slice.
- AllTrue PR [#2155](https://github.com/jerry200176-png/AllTrue_System/pull/2155)
  was subsequently merged as `c44ea6aff907d79f8ea80da56edd06619e899e32`.
  Deploy run [33167200741](https://github.com/jerry200176-png/AllTrue_System/actions/runs/33167200741)
  passed exact-SHA deployment, health, read-only API smoke, bundle checks, and
  director endpoint probes. Production `version.json` returned the same SHA
  and health remained `ok`; the authenticated UI smoke gate for this PR was
  already green before merge.
- Sunrise `https://sunrise-cafe-six.vercel.app/api/version` returned commit
  `f8927b174b04ff7e026be5f4cb341396e1d120c6`; booking health returned `ok`,
  with the existing documented degraded per-isolate rate-limit mode and
  Stripe disabled. No deploy or production mutation was performed.
- Workspace inventory found 9 repositories under `/home/jerry/workspace`:
  canonical AllTrue is dirty and 279 commits behind its remote-tracking ref;
  canonical Sunrise is dirty and 45 commits behind; Portfolio Ops is dirty.
  Legacy AllTrue checkouts under `/home/jerry/alltrue*` remain evidence-only
  and were not edited. The isolated AllTrue UI worktree and this Portfolio Ops
  worktree were created through `agent-start`.

## Reproducible read-only commands

```text
gh repo list jerry200176-png --limit 100
gh api repos/jerry200176-png/<repo>/issues?state=open&per_page=100
gh api repos/jerry200176-png/<repo>/pulls?state=open&per_page=100
gh pr checks <number> --repo jerry200176-png/<repo>
bash scripts/workspace-inventory.sh <output.tsv> /home/jerry/workspace
```

This refresh does not close additional issues, merge PRs, delete branches,
change labels, or modify production data. The #2157 merge/deploy was performed
by the existing AllTrue release flow; this report records its read-back only.
The earlier #911 closure and #2154 release are recorded above as completed
evidence.
