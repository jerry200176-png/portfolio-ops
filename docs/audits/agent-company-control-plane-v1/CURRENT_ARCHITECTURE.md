# CURRENT_ARCHITECTURE — Agent Company Control Plane Audit V1

**Audit ID:** `AGENT_COMPANY_CONTROL_PLANE_AUDIT_V1`  
**Date (UTC):** 2026-09-17  
**Nature:** Read-only evidence inventory. Claims distinguish lifecycle stages.

| Lifecycle | Meaning used here |
|-----------|-------------------|
| CODE_WRITTEN | Source exists in a repository tip |
| TESTS_PASSED | Automated tests observed green for that code |
| MERGED | Landed on the default branch |
| DEPLOYED | Exact SHA present on a runtime (prod/staging) |
| RUNTIME_VERIFIED | Behavior observed on a live process/DB/endpoint |
| OPERATIONALLY_ACCEPTED | Explicit human acceptance artifact |

---

## 1. Executive map (what actually exists)

The Jerry/AllTrue agent system is **not one control plane**. It is a **federation of overlapping layers** with fragmented authority:

```
┌──────────────────── Founder / Cursor chat ────────────────────┐
│  ad-hoc Supervisor prompts + state/alltrue/*.json flood       │
└──────────────┬───────────────────────┬────────────────────────┘
               │                       │
   ┌───────────▼──────────┐   ┌────────▼────────────────┐
   │ AllTrue harness      │   │ portfolio-ops agent_graph│
   │ scripts/harness/*    │   │ event-sourced Run/Attempt│
   │ CODE MERGED H0–H4b   │   │ CODE MERGED; scheduler   │
   │ LIVE DB schema v1 ⚠  │   │ systemd DISABLED         │
   └───────────┬──────────┘   └────────┬────────────────┘
               │                       │
               └───────────┬───────────┘
                           │
               ┌───────────▼───────────┐
               │ agent-control gateway │
               │ worktrees + sessions  │
               │ RUNTIME_VERIFIED      │
               └───────────┬───────────┘
                           │
        workers: Codex / Claude / Cursor / cubelv[bot]
                           │
               ┌───────────▼───────────┐
               │ GitHub + GH Actions   │
               │ CI / Deploy-to-Pi     │
               └───────────┬───────────┘
                     ┌─────┴─────┐
                     ▼           ▼
                   Pi PROD     Daan STAGING
```

---

## 2. Component inventory (evidence-backed)

### 2.1 AllTrue harness — product delivery control plane

| Item | Path / evidence | Maturity |
|------|-----------------|----------|
| Task/program SM | `scripts/harness/{states,transitions,store,graph}.py` | MERGED (H0–H1 ACCEPTED) |
| GoalContract / Evidence / DecisionReceipt / leases | `contracts.py`, `leases.py`, `governance_adapter.py` | MERGED (H2–H2.1 ACCEPTED) |
| Planner | `planner.py` | MERGED (H3 ACCEPTED) |
| DispatchAttempt CAS | `dispatch.py` | MERGED PARTIAL (#3022) |
| WorkerRun start/attach/resume | `worker_run.py`, `launcher.py` | MERGED (#3025 H4b @ `6932c473`) |
| CLI | `python3 -m scripts.harness …` | CODE_WRITTEN |
| Live DB | `/home/jerry/workspace/state/alltrue/harness.sqlite` | **RUNTIME schema_version=1** — missing `worker_runs`, `dispatch_attempts`, `goals`, `decision_receipts`, `checkpoints` |
| Code schema | `SCHEMA_VERSION = 4` on `origin/main` | MERGED but **not applied** to live DB |

**Critical contradiction:** H4b WorkerRun is MERGED; the live orchestrator DB cannot store WorkerRuns. Operational supervisor truth remains JSON files under `state/alltrue/`.

### 2.2 portfolio-ops `agent_graph` — event-sourced scheduler plane

| Item | Path | Maturity |
|------|------|----------|
| Event store + reducer | `agent_graph/{sqlite_store,reducer,durable_runtime}.py` | MERGED on portfolio-ops `9b41bbe` |
| Scheduler loop | `scheduler.py` (`AutonomousSchedulerLoop`) | CODE_WRITTEN |
| systemd unit | `~/.config/systemd/user/graph-scheduler.service` | **inactive / disabled** |
| Dogfood SQLite | `state/portfolio-ops/graph-control-sched-dogfood.sqlite` | RUNTIME_VERIFIED (dogfood; 10 events / 10 runs observed) |
| GitHub/deploy adapters | `github_observe.py`, `github_mutate.py`, `deploy_observe.py` | CODE_WRITTEN |
| Worktree bind | `worktree_bind.py` → agent-start | CODE_WRITTEN |

**Competing model:** `Attempt`/`Run` ≠ AllTrue `DispatchAttempt`/`WorkerRun`. Two lease/fencing designs.

### 2.3 agent-control — launch / isolation gateway

| Item | Path | Maturity |
|------|------|----------|
| Gateway | `/home/jerry/workspace/agent-control/` (not a git repo; installed from portfolio-ops) | RUNTIME_VERIFIED v0.5.1 |
| `agent-start` / `--attach` / `--resume` | `bin/agent-start` → `~/.local/bin` | RUNTIME_VERIFIED |
| Session manifests | `sessions/*.json` (~1011) | RUNTIME_VERIFIED |
| Worktree GC | `agent-finish`, `agent-worktree-audit` | CODE_WRITTEN |
| Deploy waiter | `wait-github-deploy` | RUNTIME_VERIFIED (polls Actions + Pi tip URL) |

### 2.4 Operational JSON “supervisor plane” (de-facto authority today)

Under `/home/jerry/workspace/state/alltrue/`:

- `CURRENT_STATE.json`, `CONTROL_PLANE_CANONICAL_STATE.json`
- `FOUNDER_INBOX.json`, `DELIVERY_CLOSURE_QUEUE.json`
- `DISPATCH_*.json`, `SUPERVISOR_CYCLE_*.json`, `WORKER_REGISTRY.json`
- `goals/**/GOAL.json`, EI signal files, Restate PoC artifacts

**Maturity:** OPERATIONALLY used; **not** a durable event log; **does not survive** as a coherent store across schema evolution; chat history still often used as memory.

### 2.5 ExoProtocol — repo governance kernel

| Item | Maturity |
|------|----------|
| `repos/exoprotocol`, `exo` CLI, `.exo/` locks/receipts | CODE_WRITTEN for onboarded repos |
| Role | Ticket/session fencing for *repo* work — not product WorkerRun authority |

### 2.6 engineering-intelligence

Research pipeline only (`engineering-intelligence/src/ei/*`). Explicitly **does not** wake workers, open PRs, or own leases. EI JSON under `state/alltrue/EI_*.json` are supervisor-written signals, not an automated feedback loop.

### 2.7 Restate durable-wake PoC

| Item | Path | Maturity |
|------|------|----------|
| PoC | `state/alltrue/pocs/restate-durable-wake/` | POC_ONLY + local RUNTIME_VERIFIED |
| Verdict | `ADOPT_RESTATE_SPINE` (recommendation) | **not** PRODUCTION_ADOPTED; **not** AUTHORITATIVE_CONTROL_PLANE |

### 2.8 Product surfaces mistaken for control-plane intake

- In-App BugReport (Laravel/Vue) = **product feature**, not harness intake.
- Control-plane “intake” today = Founder/Supervisor reading Issues + writing JSON / prompts.

---

## 3. Competing sources of truth

| Conflict | Evidence |
|----------|----------|
| harness code v4 vs live DB v1 | `store.py SCHEMA_VERSION=4` vs `sqlite meta schema_version=1` |
| JSON supervisor vs SQLite harness | `CURRENT_STATE.json` referenced from harness meta; WorkerRuns not in DB |
| AllTrue harness vs portfolio-ops agent_graph | Two schedulers, two lease models |
| Shared portfolio-ops checkout vs bare tip | Checkout often behind / missing `.py`; bare `9b41bbe` has full `agent_graph/` |
| Forbidden shared AllTrue checkouts vs task worktrees | AGENTS.md bans shared trees; they still exist |
| Prod tip naming | Public `daan.lifenet.com.tw` = **Pi production**, not Daan server |
| AUTONOMY_POLICY copies | Older shared checkout still shows “Merge: No”; tip policy allows R0–R3 agent merge |

---

## 4. Physical execution resources (roles from evidence)

| Name | Actual role | Authority |
|------|-------------|-----------|
| **Jerry WSL** | Supervisor + coding workers + local Restate PoC + GH Actions self-hosted runner | Code/PR/reconcile; no Pi SSH secrets by design |
| **Pi** (`pi.lifenet.com.tw` / public `daan.lifenet.com.tw`) | **Production** PHP/Laravel + MySQL | Deploy only via `deploy.yml` + Founder Environment gate |
| **Daan** (`alltrue.daan.lifenet.com.tw`) | Staging Docker + co-resident Dify/Hermes | Founder-interactive Docker; agents `NO_NEW_MUTATION` while incident open |
| **CubeLV** | **Coding agent identity** (`cubelv` / `cubelv[bot]`), not a host | Untrusted PR author under normal CI gates |

---

## 5. What is unusually strong (evidence)

1. **Risk/governance fencing for product** — `autonomy_gate`, DecisionReceipt, production Environment, exact-SHA deploy readbacks (`version.json` / `deployment.json`).
2. **Worktree isolation + provenance** — agent-control manifests with `provenance_type`, denylist, attach/resume.
3. **Lifecycle vocabulary** — MERGED ≠ ACCEPTED discipline is practiced in state artifacts.
4. **Harness contract design** — GoalContract / PlanResult / DispatchAttempt / WorkerRun is a coherent *design* on main (even if runtime cutover incomplete).
5. **Staging immutability fix** — #3036 MERGED; host checkout mutation defect closed in code.

---

## 6. What is fragile / “fake automation”

1. Supervisor loop = Cursor session + JSON files, not a durable daemon.
2. Live harness DB does not match MERGED schema → WorkerRun “exists” only as code/tests.
3. CI failure → worker wake requires Supervisor/Founder paste (`EI_ACTIONABLE_CI_WORKER_NOT_AUTO_WOKEN`).
4. Dual control planes (harness + agent_graph) without a single authority cutover.
5. ~267 AllTrue worktrees + ~1011 sessions — GC is manual/semi-manual.
6. Graph scheduler systemd unit present but disabled — looks like automation; is not running.

---

## 7. Docs / plans that are not runtime

- `ALLTRUE_AGENT_SOFTWARE_COMPANY_OPERATING_PLAN.md` — contract/plan (APPROVED for T0–T2 narrative); not an executor.
- `AI_COMPANY_UI_*` — PLAN_ONLY.
- `GRAPH_ENGINEERING_*` JSON — supervisor backlog vocabulary; not an executable graph.
- Archive `docs/archive/control-plane-shadow-v1/` — retired PDP.

---

## 8. Evidence index (architecture)

| Artifact | Location |
|----------|----------|
| AllTrue main tip (audit) | `a454475a25b883d91a605cef873eddfd3381efe8` (#3037) |
| Prod tip (Pi) | `16e38fb969cf73a227a86c4dfe9918078b00a459` |
| H4b merge | PR #3025 → `6932c473` |
| Harness live DB | `state/alltrue/harness.sqlite` (schema v1) |
| Graph dogfood DB | `state/portfolio-ops/graph-control-sched-dogfood.sqlite` |
| Canonical reconcile | `state/alltrue/CONTROL_PLANE_CANONICAL_STATE.json` |
| Restate PoC | `state/alltrue/pocs/restate-durable-wake/` |
| agent-control | `/home/jerry/workspace/agent-control/` |
| This audit worktree | `tasks/portfolio-ops/control-plane-audit-v1` @ `chore/task-control-plane-audit-v1` |
