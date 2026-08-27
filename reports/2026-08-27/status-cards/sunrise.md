# Sunrise Cafe — Status Card (2026-08-27)

**Positioning:** Cafe booking and ordering platform.
**Primary users:** Customers and cafe staff.
**Job-to-be-done:** Accept and operate bookings reliably while keeping payment
and rate-limit states explicit.

## Production

- Status: live — commit `f8927b174b04ff7e026be5f4cb341396e1d120c6`
- Health: `/api/booking-health` returned `ok=true`, 2026-08-27 10:04 +08:00
- Runtime flags: `rate_limit_grade=degraded_per_isolate`; `stripe_enabled=false`

## Open work

- Open issues: 4; open PRs: 3
- P0: 0
- P1: 3 — deploy-owner verification, portfolio/design SSOT, and Founder decision queue

## Signals

- Gmail was not re-triaged in this freshness-only pass.
- The deployed version endpoint matches the current remote `main` identity;
  this confirms serving identity, not dashboard ownership or quota capacity.

## Risks

- Top reliability risk: rate limiting remains degraded per isolate and is not
  evidence of a shared production limiter.
- Top UX friction: deployment/capacity ownership still needs dashboard-level
  verification before future releases are assumed safe.
- Top observability gap: no fresh dashboard/API evidence was collected for
  Vercel project ownership in this pass.

## This round

- Highest-ROI next action: complete read-only Vercel dashboard ownership and
  deploy-owner verification; keep paid-plan and migration decisions gated.
- Founder decisions needed: Vercel capacity/plan and any Supabase production
  migration or paid-infrastructure changes.
