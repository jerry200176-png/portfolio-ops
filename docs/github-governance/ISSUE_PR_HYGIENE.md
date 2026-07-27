# Issue & PR Hygiene — 2026-07

No bulk closes performed. Classifications are recommendations.

## Portfolio snapshot

| Repo | Open Issues | Open PRs | Draft PRs | Notes |
|---|---:|---:|---:|---|
| `jerry200176-png/AllTrue_System` | 76 | 11 | 4 | labels=44, milestones=6 |
| `jerry200176-png/alltrue_studyplan` | 0 | 0 | 0 | labels=9, milestones=0 |
| `jerry200176-png/income-statement-app` | 0 | 0 | 0 | labels=9, milestones=0 |
| `jerry200176-png/income-statement-app-releases` | 0 | 0 | 0 | labels=9, milestones=0 |
| `jerry200176-png/korea-trip-plan` | 1 | 1 | 1 | labels=9, milestones=0 |
| `jerry200176-png/portfolio-ops` | 0 | 1 | 0 | labels=9, milestones=0 |
| `jerry200176-png/student-evaluation` | 0 | 0 | 0 | labels=9, milestones=0 |
| `jerry200176-png/sunrise-cafe` | 4 | 1 | 0 | labels=24, milestones=0 |
| `jerry200176-png/vibe-app-store` | 0 | 0 | 0 | labels=9, milestones=0 |

## AllTrue_System — operating model stress

Evidence: 76 open issues, 11 open PRs (4 draft). Multiple concurrent bot stacks (`cubelv[bot]`) plus human/agent drafts. Risk = founder decision queue saturation + superseded stacks.

### Open PRs classification

| PR | Class | Rationale |
|---|---|---|
| #1457 `cubelv-cli-binding-mgmt-ui-9a6df66c` | needs evidence | draft=False; user=cubelv[bot]; updated=2026-07-27; [W31][P1-4] feat(frontend): LINE 綁定管理頁面 |
| #1456 `cubelv-cli-cleanup-orphan-bindings` | needs evidence | draft=False; user=cubelv[bot]; updated=2026-07-27; [W31][P1-3] feat(binding): add CleanupOrphanBindings command with sche |
| #1455 `cubelv-cli-changelog-pr1452-d47e62f1` | actionable | draft=False; user=cubelv[bot]; updated=2026-07-27; docs(changelog): expand PR #1452 — CI governance failure taxonomy + fa |
| #1454 `cubelv-cli-phase4-tests` | needs evidence | draft=False; user=cubelv[bot]; updated=2026-07-27; test(dashboard): Phase 4 test scaffolding — CampusSnapshotFactory + 5  |
| #1453 `cursor/ci-gov-reviewability-1ff7` | waiting for human decision | draft=True; user=jerry200176-png; updated=2026-07-27; ci(governance): make PR reviewability risk-based and base-aware |
| #1418 `docs/1401-closure-packet` | waiting for human decision | draft=True; user=jerry200176-png; updated=2026-07-25; docs(incident): #1401 closure packet |
| #1417 `sec/provenance-founder-exception` | waiting for human decision | draft=True; user=jerry200176-png; updated=2026-07-25; sec(governance): narrow, auditable founder-exception provenance path |
| #1410 `feat/course-continuity-mvp` | actionable | draft=False; user=jerry200176-png; updated=2026-07-24; feat(continuity): Course Continuity group API MVP (#1382) |
| #1409 `fix/epic-a-d-residual` | actionable | draft=False; user=jerry200176-png; updated=2026-07-24; fix(schedule): Epic A/D residual — shared filter + in-dialog errors +  |
| #1402 `fix/schedule-occurrence-stability` | actionable | draft=False; user=jerry200176-png; updated=2026-07-24; fix(schedule): series vs occurrence stability after 調課 |
| #1399 `fix/early-settle-usage` | stale but valuable | draft=True; user=jerry200176-png; updated=2026-07-24; feat(billing): early usage settlement (提前結清) |

### Labels
AllTrue label count: 44. Sample: area:attendance, area:backups, area:billing, area:ci, area:db, area:docs, area:engagement, area:finance, area:import, area:ops, area:parent-portal, area:review, area:security, area:testing, area:ui, bug, ci-enforcement, dependencies, documentation, duplicate, enhancement, github_actions, good first issue, help wanted, high-priority, invalid, javascript, phase-0, php, platform, priority:p0, priority:p1, priority:p2, priority:p3, question, risk-ack-no-test, security, status:blocked, status:needs-decision, status:ready…

Observation: rich label taxonomy exists; priority semantics likely overloaded across bug/sec/ops. Recommend documenting label SSOT in portfolio-ops (not inventing new labels yet).

## Sunrise
- PR #253: `feat(ui): establish Sunrise guest landing and admin operations shell` — class: **actionable** (active UI redesign); watch Agent Provenance flake historically.
- Open issues: 4 — keep linked to Vercel capacity / SEC decisions in portfolio.yaml.

## portfolio-ops
- Open PR #9 `feat/portfolio-mission-loop-harness` — **actionable / needs review**.
- Merged branches not deleted — see BRANCH_CLEANUP_CANDIDATES (high confidence).

## korea-trip-plan
- Draft PR #28 — **waiting for human decision** or continue later; many merged cursor branches are safe close/delete candidates.

## Safe close candidates (Issues/PRs)
_None auto-closed. Only propose closes when duplicate/superseded evidence is explicit; none elevated to execute without Founder._

## Umbrella Issue strategy
Create one portfolio Issue on `portfolio-ops`: `GitHub Platform Governance Audit — 2026-07` linking these docs; spawn child Issues per approved remediation workstream (not one Issue per finding).
