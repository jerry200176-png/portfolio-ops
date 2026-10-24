# Portfolio narrative

Structured observations live in `portfolio.yaml`; the current bounded evidence
is [reports/2026-10-24/portfolio-reference-refresh.md](reports/2026-10-24/portfolio-reference-refresh.md). This file describes products and the working
model, rather than treating an old operational snapshot as current.

## AllTrue System — Tier 0

Multi-campus tutoring operations: attendance, billing and scheduling for school
staff, instructors and parents. It is self-hosted on a Raspberry Pi at
`daan.lifenet.com.tw` and handles minors' PII and billing data.

At source commit `219c4ab0bca2d79fece44646b2457bc80acbcba0`, the application is Vue 3 / Vite with a
Laravel 8 / PHP 8.2 / MySQL backend. `frontend/src/supabase.js` is its own
`/api/v1` adapter; its name is not evidence of a hosted Supabase backend.
LINE push/webhook handlers and tests coexist with Telegram handlers.
Filament/Livewire is not the checked application UI stack; a reference-library
entry is not an installed dependency. See the pinned source links in the report.

## Sunrise Cafe — Tier 0

Cafe booking/ordering for customers and staff, deployed through Vercel with a
Supabase backend. Source observations use `73416404bfd55872b7354e477c959b68d4deb331`. Public booking health
still reports the in-memory, per-isolate rate limiter as degraded; this refresh
does not fix or activate a limiter, reminder or deposit-cancellation workflow.

## Work paths and infrastructure

RULEBOOK section 9 defines the current model: cloud session, fresh clone,
task branch, PR. Work in the actual session checkout. The old bare-store,
task-root and duplicate-checkout paths remain historical discovery records;
they are not cloud paths or permission to edit existing user directories.
AllTrue's listed forbidden checkouts remain forbidden.

- Portfolio Ops is the governance/evidence repository, not a product runtime.
- `agent-control/`, local preflight/session provenance and ExoProtocol are
  retired requirements, not canonical launchers or active pilots.
- Private research and other workstation projects were not re-inventoried;
  their existing public names do not imply fresh access or implementation evidence.

## Change log

- 2026-10-24: corrected current navigation and AllTrue stack from pinned source;
  refreshed public repository/Star/label and runtime observations; retained
  product acceptance and workstation/private-project state as unverified.
- 2026-10-14: current cloud-session/retirement decision is recorded in
  RULEBOOK section 9; older local-path instructions below are historical.
- 2026-09-04 (historical): introduced the bare+tasks inventory and then-current
  product observations. This was not a current cloud launch contract.
- 2026-08-27 (historical): rebaselined around the AllTrue director workflow incident.
- 2026-07-25 (historical): renamed `company-os` to `portfolio-ops`.
