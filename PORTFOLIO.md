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

**Canonical agent write path:** `agent-start alltrue <task-id>` →
`/home/jerry/workspace/tasks/alltrue/<task-id>/` on bare
`/home/jerry/workspace/repos/AllTrue_System.git`. Legacy checkouts
(`/home/jerry/alltrue`, `workspace/AllTrue_System`,
`workspace/AllTrue_System-clean`) are forbidden for agent edits.

## Sunrise Cafe — Tier 0

Public-facing cafe booking/ordering platform for customers and cafe staff.
Deployed on Vercel with a Supabase backend. No stored card data. Agent writes
go through `agent-start sunrise <task-id>`. Required GitHub checks for merge
are Lint & Build, Playwright smoke, and Agent Session Provenance.

## Non-product infrastructure

- `agent-control/` — **canonical** session launcher/preflight. Not a product.
- `portfolio-ops/` (this repo) — the control plane itself.
- ExoProtocol — **experiment only**; not a required fleet gate.
- `engineering-intelligence/` — read-only research pipeline relative to products.
- `income-statement-app` (+ releases) — separate desktop product.

## Change log

- 2026-09-04: converged AllTrue/Sunrise path model to bare+tasks, refreshed
  inventory against live production identity, enforced Sunrise required
  checks, demoted Exo to experiment, and reset autonomy to risk-based
  Agent operator (Founder only for irreversible/high-blast risk).

- 2026-08-27: rebaselined the portfolio around the AllTrue director workflow
  incident. Recorded the production SHA/health evidence and PR #2086.

- 2026-07-25: restructured from `company-os` into `portfolio-ops`.
