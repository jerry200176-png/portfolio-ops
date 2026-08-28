# GitHub portfolio triage — 2026-08-28

Capture time: 2026-08-28 18:52 +08:00. Source of truth for repository and
collaboration state: GitHub API/`gh` read-back in this session. Labels are
signals only; the shortlist below is cross-checked against PR checks, local
worktrees, and production read-only endpoints.

## Portfolio snapshot

| Repository | Open issues | P1-labelled | Blocked-labelled | Open PRs | Immediate signal |
|---|---:|---:|---:|---:|---|
| [AllTrue System](https://github.com/jerry200176-png/AllTrue_System) | 73 | 33 | 38 | 5 | UI PR #2129 fails size and UI smoke gates; safety/reliability work remains higher risk |
| [Engineering Intelligence](https://github.com/jerry200176-png/engineering-intelligence) | 0 | 0 | 0 | 1 | PR #1 has failing checks and is the only open delivery item |
| [Portfolio Ops](https://github.com/jerry200176-png/portfolio-ops) | 2 | 0 | 0 | 6 | PR #40 is draft/failing; dependency and governance PRs otherwise have no recorded failure |
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
| AllTrue | [#2129](https://github.com/jerry200176-png/AllTrue_System/pull/2129) | Open; Presubmit and UI Smoke failed; Vite build passed | Split the 1,279-line UI change into reviewable slices and repair the course-management smoke contract before review |
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

1. [#2086](https://github.com/jerry200176-png/AllTrue_System/pull/2086) —
   production-sensitive eighth-session workflow; the current portfolio queue
   still requires independent review and serving-SHA verification.
2. [#2002](https://github.com/jerry200176-png/AllTrue_System/issues/2002) —
   cross-date reschedule/calendar consistency; requires a reviewed projection
   contract before any materialization or data repair.
3. [#2129](https://github.com/jerry200176-png/AllTrue_System/pull/2129) —
   broad UI refactor; failed size/UI gates prove it is not a release candidate.
4. [#911](https://github.com/jerry200176-png/AllTrue_System/issues/911) —
   director drill-down and explanation layer; the new daily progress V1 is a
   bounded implementation slice for this issue.
5. [#1618](https://github.com/jerry200176-png/AllTrue_System/issues/1618) —
   teacher daily workflow; follow after the director pattern is measured.

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

- AllTrue `https://daan.lifenet.com.tw/version.json` returned HTTP 200 with
  serving build SHA `4a6b2a3276f69e32e627dc1cb1930c37fee2ef91`, and
  `https://daan.lifenet.com.tw/api/v1/health` returned `{"status":"ok"}`.
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

This report does not close issues, merge PRs, delete branches, change labels,
deploy, or modify production data. Those remain separate governed actions.
