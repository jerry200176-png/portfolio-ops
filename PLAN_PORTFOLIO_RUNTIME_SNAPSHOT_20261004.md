# Plan: correct portfolio runtime and blocker snapshot

## Goal

Make the public portfolio report distinguish a healthy runtime from an explicitly degraded runtime, and publish exact current runtime/candidate/blocker evidence without treating stale inventory or unknown product acceptance as normal.

## Scope and risk

T0 reporting and evidence generation in portfolio-ops only. No product workflow, deployment, activation, private source data, or production write. Production reads use the already-configured public version/health endpoints and read-only GitHub API.

## Verified inputs (2026-10-04 UTC)

- Portfolio Ops base: `55a9eca71906162bc98730936aba50af14e16fb3`.
- AllTrue runtime: `e483c1dc43975cfa173b12e75376fa51dc107a30`, health `status=ok`.
- AllTrue candidate: `21cd3e0f2b75114ba66f9f59b6cde9edd87b3f2c`; 14 commits ahead of production, run `37193508312` waiting in `production-activation`; GitHub reports required reviewer, exact workflow job `Founder production approval (same run)`. No run artifacts/digest available.
- Sunrise runtime/main: `fec9e458767bd5b4a0e51cb440d4145440591ecc`; health returns `ok=true`, `rate_limit_mode=memory`, `rate_limit_grade=degraded_per_isolate`.
- Sunrise reminder backup run `37139788688` failed at `2026-10-03T17:16:03Z` with `MIDDLEWARE_INVOCATION_FAILED`; detailed Vercel cause and any second-call side effect are unknown. No rerun is authorized by this plan.
- Existing `portfolio.yaml` inventory verification is from 2026-09-04 and will remain visibly stale; this change does not claim a full portfolio/issue triage refresh.

## Steps

1. Extend the read-only production identity classifier to preserve explicit degraded and unhealthy health separately from the observed serving SHA.
2. Add focused regression coverage for a healthy service carrying a degraded rate-limit signal, and for explicitly unhealthy runtime.
3. Regenerate the timestamped JSON/Markdown runtime report using current endpoints and GitHub evidence; include the current AllTrue waiting candidate, explicit environment review blocker, Sunrise degradation, and reminder incident. Keep candidate/artifact/acceptance fields `UNKNOWN` where evidence is unavailable.
4. Update only the current dashboard summary/pointer, preserving stale inventory and historical sections.
5. Run focused/full required local checks, freshness and changed-path gate, inspect the report/diff, and obtain independent review.

## Acceptance

- AllTrue is `RUNTIME_VERIFIED` at the exact production SHA, separately from the waiting candidate and protected review gate.
- Sunrise's serving SHA is visible and its runtime health is `DEGRADED`, never `HEALTHY`, while the rate-limit mode/grade is present.
- Reminder failure is shown as a separate observed incident with root cause and completion state marked unknown; no rerun occurs.
- Artifact digests and product acceptance remain unknown absent direct evidence.
- Portfolio inventory/issue freshness remains explicitly stale until full triage; no stale values are refreshed by implication.
- No GitHub or production side-effect workflow is dispatched.
