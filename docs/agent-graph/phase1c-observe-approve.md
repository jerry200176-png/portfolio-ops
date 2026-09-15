# Phase 1C — Observation + Founder Approval

## External observation

Read-only adapters (`gh pr view` / checks) produce `ObservableFact` values.
Ingestion path: Observation → verifier → `EXTERNAL_OBSERVATION` Event → reducer.

Adapters never choose graph transitions and never mutate GitHub.

## Exact-SHA binding

Every PR/CI fact carries `observed_head_sha`. CI green for SHA A does not
authorize SHA B. `PR_HEAD_OBSERVED` with a new SHA invalidates prior approval
and supersedes CI authority for the old SHA.

## Founder Approval

Canonical Founder-risk policy remains:

- `docs/fleet-merge-policy.md` (R3 / Founder-risk)
- `governance/AUTONOMY_POLICY.md`
- `governance/company-agent-contract.yaml` (`irreversible_actions`)

`docs/verify-retry-loop.md` T0–T3 is inner-loop eligibility, not a second
merge ladder. Graph `risk_tier` values `R3`/`T3`/`founder*`/`high` map to
Founder-required waiting at `human_gate`.

Approval is written only via control-plane CLI:

`graph approve RUN_ID --action … --head-sha …`

Workers cannot propose `HUMAN_APPROVED` / `HUMAN_REJECTED`.

## Phase terminal

`HUMAN_APPROVED` routes to `approved_for_effect` (no merge/deploy).
Effect Journal is a declare-only stub in this phase.
