# Daily operating loop

## Schedule

- Daily company patrol: 08:30 Asia/Taipei
- Immediate P0/P1 follow-up: every patrol and whenever a current task wakes
- Weekly governance and portfolio review: Monday 09:00 Asia/Taipei

## Daily sequence

1. Read Company OS and fresh capability registry.
2. Inspect both canonical repository states and fetch origin.
3. Inspect open PRs, review threads, required checks, recent failed workflows, and deployment state.
4. Verify production health and release identity for both products.
5. Triage Gmail: security/production/customer first, then GitHub/CI, then business, then noise.
6. Update `state/work-queue.yaml` using company priority order.
7. Enforce WIP limit: one production-affecting implementation per product.
8. Execute the highest-value unblocked item end-to-end: reproduce, plan, implement, test, PR, review, CI, merge, deploy, production verify, documentation, communication.
9. Record a daily report under `reports/daily/` and update durable lessons or policy when needed.

## Reporting

Daily report:

- production health and release identities
- P0/P1 incidents
- PR/CI/deploy state
- Gmail urgent/needs-reply/waiting/FYI buckets
- completed outcomes with evidence
- current WIP and next action
- blocked external capabilities or spending

Weekly report adds security posture, dependency health, DORA-style delivery signals, product KPI trends, governance drift, stale work, and new-project proposals.
