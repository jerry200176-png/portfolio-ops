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

The actual step-by-step procedure lives in
`.claude/skills/portfolio-maintain/modes/triage.md` (and `execute.md` for
the implementation half) — invoke it, don't re-derive it here. This file
covers cadence and reporting standard; the skill is the single source of
truth for the steps themselves, so the two can't drift apart.

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
