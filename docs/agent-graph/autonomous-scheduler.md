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

## Service form

Optional systemd user unit:

```bash
chmod +x scripts/install-graph-scheduler-user-unit.sh
./scripts/install-graph-scheduler-user-unit.sh
systemctl --user start graph-scheduler.service
```

Operational queries (no dashboard):

```bash
python3 -m agent_graph.cli --db ~/workspace/state/portfolio-ops/graph-control.sqlite schedule-status
systemctl --user status graph-scheduler.service
```

## Schedule-driven dogfood

Run `GRAPH_REAL_CODEX=1 python3 scripts/graph-schedule-realcodex-dogfood.py` to drive a RealCodex R1 maintenance Run via `AutonomousSchedulerLoop` (no manual `schedule-tick`).

On success, evidence is written to `reports/<date>/schedule-realcodex-dogfood/{SUMMARY,EVIDENCE,trace}.json`.
