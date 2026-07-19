# New project intake and governance

No new project receives autonomous write or deployment authority until this intake is committed.

## Required charter

1. Customer problem and target user
2. Measurable 90-day outcome and kill criteria
3. Product owner and operational owner
4. Repository, license, visibility, and data classification
5. Architecture and external dependencies
6. Authentication, authorization, tenancy, PII, payment, and regulatory boundaries
7. Environments, deployment authority, rollback, backup, restore, monitoring, and SLO
8. Testing pyramid, required checks, dependency/security scanning, and production verification
9. Gmail/GitHub communication channels and escalation policy
10. AI autonomy overlay and capability evidence

## Stage gates

| Stage | Exit evidence |
|---|---|
| Explore | Problem evidence, alternatives, 90-day metric, kill criteria |
| Incubate | Threat model, architecture decision, prototype test, cost ceiling |
| Build | Repo controls, CI, tests, preview environment, runbook |
| Launch | Production identity, rollback, backup/restore, monitoring, support path |
| Operate | Daily signals, incident policy, KPI review, dependency cadence |
| Retire | Export/retention plan, user communication, credential and infrastructure teardown |

Projects that cannot satisfy a gate remain in the prior stage; documentation alone does not advance a stage.
