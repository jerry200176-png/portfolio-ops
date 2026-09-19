# EXECUTIVE_RECOMMENDATION

**Audit:** `AGENT_COMPANY_CONTROL_PLANE_AUDIT_V1` · 2026-09-17

---

## 1. Where we are

AllTrue already has **unusually strong product-delivery governance** (risk tiers, exact-SHA deploy, DecisionReceipt design, worktree isolation) and a **coherent harness design on `main` (H0–H4b)**.  

What it does **not** yet have is a **running company control plane**: the live harness DB is still schema v1, the Supervisor loop is a Cursor session + JSON flood, CI failures require paste-wakes, and a second event-sourced scheduler (`agent_graph`) is MERGED but systemd-disabled.

**Distance to target:** roughly **one durable SoT cutover + one event-wake spine** away from “autonomous intake→dispatch→verify” for T0–T2 work — not a greenfield rewrite, and not a Kubernetes platform.

## 2. Five biggest missing capabilities

1. **Live durable task identity** (WorkerRun in authority store)  
2. **External event inbox + CI auto-wake**  
3. **Durable Supervisor tick** (survives chat restart)  
4. **Canonical intake/dedup** (In-App/Issues → WorkItem)  
5. **Founder Console on real projections** (after 1–4)

## 3. Build / adopt / delete (headline)

| Action | Target |
|--------|--------|
| HARDEN | AllTrue harness + agent-control + autonomy_gate/deploy fences |
| ADAPT | Restate for wake/inbox only (Gate-1 next) |
| ADAPT (later) | Restate UI + custom Founder boards |
| DEFER | Temporal, K8s, SWE-ReX replace, A2A mesh, LangGraph-as-OS |
| DELETE/park | Dual live schedulers; CubeLV-as-machine myth; unused CAO confusion |

## 4. Next single bounded Goal (DO NOT START HERE)

### `HARNESS_STORE_AUTHORITY_CUTOVER`

**Objective:** Make `harness.sqlite` schema v4+ the sole authority for Program/Task/DispatchAttempt/WorkerRun/leases/escalations; emit `CURRENT_STATE` as a projection; prove Supervisor restart reattaches without Founder paste for one dogfood WorkerRun.

**Must not:** adopt Restate into prod, build UI, enable graph-scheduler, mutate Pi/Daan, expand product features.

**Exit evidence:** migrated DB backup; `worker_runs` rows for a real attach; empty contradictory JSON authority claims; tests + docs.

After that Goal succeeds, the following Goal should be `RESTATE_ADOPTION_GATE_1` (CI event → wake on real WorkerRun).

## 5. Mutation statement (this audit)

Writes limited to documentation under:

`docs/audits/agent-company-control-plane-v1/*`

on branch `chore/task-control-plane-audit-v1` in portfolio-ops worktree  
`/home/jerry/workspace/tasks/portfolio-ops/control-plane-audit-v1`.

**No** production/staging mutation, flag changes, merges of unrelated PRs, DB migrates, framework installs, or Restate/Temporal/OpenHands adoption.
