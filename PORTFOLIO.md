# Portfolio narrative

Structured, machine-maintained data lives in `portfolio.yaml` (schema:
`schemas/portfolio.schema.yaml`). This file is the human-readable narrative
companion — what each product *is* and why it matters — kept short and
updated only when that story actually changes, not every triage run.

## AllTrue System — Tier 0

School course-operations platform: attendance, billing, scheduling, for
school staff, instructors, and parents/guardians of enrolled students. Self-
hosted on a Raspberry Pi at `daan.lifenet.com.tw`. Handles minors' PII and
billing data — the highest data-sensitivity product in the portfolio.
Currently in active P0 containment (SEC-ALLTRUE-003 — see
`state/work-queue.yaml`) following a credential exposure in a public Actions
log.

## Sunrise Cafe — Tier 0

Public-facing cafe booking/ordering platform for customers and cafe staff.
Deployed on Vercel with a Supabase backend. Public repository. No stored
card data. Recent operating friction has been Vercel preview-deployment
capacity limits and an open RLS/rate-limit/backup hardening decision queue
(SEC-SUNRISE-002).

## Non-product infrastructure

- `agent-control/` — safe session launcher/preflight, used before any agent
  touches product code. Not a product; not tiered.
- `portfolio-ops/` (this repo) — the control plane itself.

## Change log

- 2026-07-25: restructured from `company-os` into `portfolio-ops` under a
  conservative autonomy policy (no autonomous merge/deploy/production-data
  mutation/Gmail mutation). See `governance/AUTONOMY_POLICY.md`.
- 2026-07-19: initial portfolio baseline established (AllTrue, Sunrise).
