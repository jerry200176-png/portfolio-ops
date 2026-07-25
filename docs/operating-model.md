# Operating model

## Cadence

- Daily patrol: on request, or via `/portfolio-maintain status` /
  `/portfolio-maintain triage` at session start.
- Weekly review: `/portfolio-maintain weekly-review` — adds security
  posture, dependency health, delivery signals, product KPI trends,
  governance drift, and stale-work cleanup on top of the daily patrol.
- There is no unattended schedule by default. If the Founder wants a cron
  loop, set it up explicitly (see the `schedule`/`loop` skills) — this repo
  does not assume one.

## Daily/triage sequence

1. Read `CLAUDE.md`, then `portfolio.yaml` and `CEO_DASHBOARD.md` for last
   known state — treat as stale until re-verified this session.
2. Inspect each Tier 0/1 repo: fetch origin, check branch/working-tree/
   stash/ahead-behind state.
3. Inspect open PRs, review threads, required checks, recent failed
   workflows, and deployment state via GitHub.
4. Verify production health and release identity (read-only: version/health
   endpoints) for each Tier 0/1 product.
5. Triage Gmail (read-only): security/production/customer signals first,
   then GitHub/CI, then business, then noise.
6. Update `state/work-queue.yaml` using the priority order in
   `docs/prioritization.md`.
7. Enforce WIP limit: at most one production-affecting implementation per
   product in flight at a time (unless a P0 incident requires interrupting
   it).
8. Execute the highest-value unblocked item through: reproduce → plan →
   implement → test → Draft PR. Stop there — merge and deploy are Founder
   decisions (see `governance/AUTONOMY_POLICY.md`).
9. Update `CEO_DASHBOARD.md` and write a dated report under
   `reports/YYYY-MM-DD/`.

## New project intake

No new project gets write access from these agents until this charter is
filled in and added to `portfolio.yaml`:

1. Customer problem and target user.
2. Measurable 90-day outcome and kill criteria.
3. Product owner and operational owner.
4. Repository, license, visibility, and data classification.
5. Architecture and external dependencies.
6. Auth, authorization, tenancy, PII, payment, and regulatory boundaries.
7. Environments, deployment authority, rollback, backup, restore,
   monitoring, SLOs.
8. Testing pyramid, required checks, dependency/security scanning,
   production verification plan.
9. Gmail/GitHub communication channels and escalation policy.

### Stage gates

| Stage | Exit evidence |
|---|---|
| Explore | Problem evidence, alternatives, 90-day metric, kill criteria |
| Incubate | Threat model, architecture decision, prototype test, cost ceiling |
| Build | Repo controls, CI, tests, preview environment, runbook |
| Launch | Production identity, rollback, backup/restore, monitoring, support path |
| Operate | Daily signals, incident policy, KPI review, dependency cadence |
| Retire | Export/retention plan, user communication, credential/infra teardown |

Documentation alone does not advance a stage — exit evidence must be real.

## Reporting

Each dated report (`reports/YYYY-MM-DD/`) should be readable standalone:
production health and release identity, P0/P1 state, PR/CI/deploy state,
Gmail signal buckets, completed work with evidence, current WIP and next
action, and any blocked capability. Weekly reports additionally cover
security posture, dependency health, delivery signals, product KPI trends,
governance drift, and stale-work candidates for archival.
