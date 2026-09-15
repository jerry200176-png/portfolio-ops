# Autonomous single-host scheduler

Graph Control Plane v1 runs a bounded scheduler/reconciler loop on one host.

## Commands

- `graph schedule-tick` — single deterministic tick (debug/tests)
- `graph schedule-run` — autonomous loop with scheduler ownership lease
- `graph schedule-status` — ownership, runnable runs, blocked runs

## Scope

- Project: `jerry200176-png/portfolio-ops` only
- Effects: existing GitHub PR allowlist (`github_pr_create|comment|merge`)
- Production deploy / DB / migration authority: **disabled**

## Ownership

One active scheduler lease per control-plane DB (`scheduler:portfolio-ops`).
Second schedulers fail closed; crash recovery uses process identity + lease reconciliation.

## Shutdown

Send `SIGTERM` to stop accepting new actions, release ownership, and exit.

## Schedule-driven dogfood

Run `GRAPH_REAL_CODEX=1 python3 scripts/graph-schedule-realcodex-dogfood.py` to drive a RealCodex R1 maintenance Run via `AutonomousSchedulerLoop` (no manual `schedule-tick`).
