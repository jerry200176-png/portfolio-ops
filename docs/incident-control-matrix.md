# Incident-to-Control Matrix

This matrix prevents closing a historical incident without adding a durable control.

| Recurrence family | Historical signal | Preventive control | Required evidence |
|---|---|---|---|
| Cross-family authorization / PII | AllTrue #1401 | scoped authorization tests, append-only auth and switch audit events, no-PII audit payload tests | test output, migration review, production read-only verification |
| Credential exposure / release identity | AllTrue #1387, #1428 | fingerprint audit, rotation runbook, backend/frontend dual-SHA manifest | workflow result, backup/restore evidence, version endpoint |
| Schedule and contract drift | AllTrue #957, #1402, #1409 | occurrence-vs-series contract, shared effective-session filter, regression fixtures | PHPUnit/Vitest, visual evidence, rollback plan |
| Billing truth divergence | AllTrue #1096, #1130, #1152 | explicit billing state transitions, reconciliation evidence, required reason for destructive actions | domain tests, audit record, owner decision |
| Deployment duplication / drift | Sunrise #257 and Vercel-capacity evidence | one deploy owner, read-only verification, bounded concurrency and backoff | workflow contract test, deployment record |
| Public booking abuse / data exposure | Sunrise #28, #67, #211 | RLS deny-by-default, explicit session/auth boundary, rate-limit degradation policy | anonymous negative tests, admin positive tests, migration gate |
| Type and regression escape | Sunrise #29, #261 | typecheck baseline, unit/E2E coverage for time/payment/booking logic | recorded SHA, CI artifact, classified failure list |
| SOP and observability drift | AllTrue #872, #873, #884, #894, #895 | postmortem template, SLO/alert owner, SOP review cadence, support SLA metrics | dated report, owner, next review, linked run/evidence |

## Operating rule

An Issue is not considered operationally complete merely because its code is merged. The control, regression test, runbook, owner, and evidence link must also exist or the item remains open/blocked in `state/work-queue.yaml`.
