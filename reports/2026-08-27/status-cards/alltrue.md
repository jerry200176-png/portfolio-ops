# AllTrue System — Status Card (2026-08-27)

**Positioning:** School operations platform for attendance, scheduling, and
billing.
**Primary users:** School staff, instructors, and parents/guardians.
**Job-to-be-done:** Let staff complete a student workflow with a clear,
auditable decision and no hidden data correction.

## Production

- Status: live — build `5e6598052299386bbf13e12ae320b90186022348`
- Health: `/api/v1/health` HTTP 200, `status=ok`, 2026-08-27 10:04:10 +08:00
- Release candidate: [PR #2086](https://github.com/jerry200176-png/AllTrue_System/pull/2086), CI green, review pending

## Open work

- Open issues: 78; open PRs: 9
- P0: 0
- P1: 33, led by the director workflow / scheduling and architecture backlog

## Signals

- Gmail was not re-triaged in this freshness-only pass.
- Production read-only booking check for Xindian StudentClass 2081 on
  2026-08-29 13:00 returned `can_add=true`, `conflict_type=none`, and one
  available session. No production row was written by this work.

## Risks

- Top reliability risk: production is still on the pre-PR #2086 build, so the
  director-facing stale-check race is not yet mitigated in production.
- Top UX friction: opening manual scheduling initially checked an invalid or
  already-past date, and an older 422 could replace the latest valid result.
- Top observability gap: an authenticated, post-deploy director acceptance
  trace still needs to be captured without exposing student PII.

## This round

- Highest-ROI next action: independent review, merge, deployment, and
  read-only post-deploy verification of PR #2086.
- Founder decisions needed: approve the production merge/deploy under the
  repository’s existing gate; any data correction remains a separately audited
  operation.
