# TARGET_ARCHITECTURE (6–12 months)

**Audit:** `AGENT_COMPANY_CONTROL_PLANE_AUDIT_V1` · 2026-09-17  
Target ≠ current. No implementation in this Goal.

---

## Canonical diagram

```
                         ┌─────────────────────────────┐
                         │     Founder Control Console │
                         │  APPROVE/REJECT/PAUSE/...   │
                         └──────────────▲──────────────┘
                                        │ projections + decisions
┌───────────────┐    events     ┌───────┴────────┐    wake     ┌──────────────────┐
│ Intake Plane  │──────────────▶│ Work Management│────────────▶│ Orchestration    │
│ In-App        │  dedupe       │ WorkItem SoT   │  plan/disp  │ Supervisor tick  │
│ GH Issues     │               │ GoalContract   │             │ Restate wake     │
│ CI failures   │               │ priority/deps  │             │ reconciler       │
│ Incidents/Ops │               │ harness.sqlite │             │ (deterministic)  │
│ Founder ideas │               └───────┬────────┘             └────────┬─────────┘
└───────────────┘                       │                               │
                                        │                         dispatch/lease
                                        │                               ▼
                                        │                      ┌──────────────────┐
                                        │                      │ Execution Plane  │
                                        │                      │ Workers (replace)│
                                        │                      │ agent-control WT │
                                        │                      │ Jerry / (cubelv) │
                                        │                      └────────┬─────────┘
                                        │                               │ PR/CI
                                        ▼                               ▼
                               ┌────────────────┐             ┌──────────────────┐
                               │ Governance     │◀────────────│ Delivery Plane   │
                               │ autonomy_gate  │  evidence   │ branch/PR/CI     │
                               │ DecisionReceipt│             │ merge/deploy Pi  │
                               │ Founder gates  │             │ stage Daan       │
                               │ fencing/budget │             │ runtime verify   │
                               └───────┬────────┘             └────────┬─────────┘
                                       │                               │
                                       ▼                               ▼
                               ┌────────────────┐             ┌──────────────────┐
                               │ Intelligence   │◀── traces ──│ Experience       │
                               │ OTel/Langfuse  │             │ Console + notify │
                               │ eval later     │             └──────────────────┘
                               └────────────────┘
```

**Authoritative stores (target):**

| Store | Owns |
|-------|------|
| `harness.sqlite` (schema ≥4) | WorkItem/Program/Task, leases, DispatchAttempt, WorkerRun, DecisionReceipt, escalations, transitions |
| Restate journal (local/ops) | Durable waits + external-event idempotency for wakes only |
| GitHub | Issues/PRs/Actions as external facts (observed, not dual-owned) |
| agent-control sessions | Physical session/worktree binding (projection into WorkerRun) |
| Pi deployment.json | Production SHA fact |
| Daan lifecycle logs | Staging evidence packets |

Chat history is **never** authoritative.

---

## Planes (responsibilities)

### Intake Plane
Deterministic adapters emit `ExternalEvent` with idempotency keys. LLM used only for ambiguous classification.

### Work Management Plane
Canonical WorkItem; dedup; priority; risk tier; GoalContract fingerprint; dependency edges (minimal).

### Orchestration Plane
Supervisor = durable tick (process supervised by systemd/Restate), not a chat session. Deterministic: reconcile, lease reclaim, CI wake routing, GC candidates. LLM: plan/code/review via workers.

### Execution Plane
Replaceable workers behind WorkerRun. Isolation = agent-control worktrees (KEEP). Capability labels route to Jerry coding vs Actions vs Daan staging job.

### Delivery Plane
Branch/PR/CI/merge/deploy/runtime-verify/rollback/acceptance as explicit states on WorkItem. Exact-SHA verification KEEP.

### Governance Plane
autonomy_gate, DecisionReceipt, Founder Environment, fencing — KEEP as AllTrue authority even if Restate wakes workers.

### Intelligence Plane
P2: traces/cost; learning loop only after intake+wake work.

### Experience Plane
Founder Console (see CONTROL_PLANE_UI_SPEC.md).

---

## Graph engineering scope (corrected)

| Use graph/LLM nodes for | Keep as plain jobs/events |
|-------------------------|---------------------------|
| understand / classify ambiguity | state transitions with CAS |
| plan / code / review / diagnose | leases, fencing, timeouts |
| | GitHub/CI reconcile, deploy observe |
| | dedup, GC, evidence validation |
| | permissions / side-effect fencing |

**Do not** encode CI polling or lease renew as LangGraph nodes.

---

## Adoption sequence (dependency order)

1. Harness store authority cutover (v4 + projections)  
2. External CI/event → WorkerRun wake (Restate Gate-1)  
3. Continuous reconciler tick (single)  
4. Intake adapters (GH + In-App)  
5. GC automation  
6. Founder Console MVP  
7. Telemetry (Langfuse/OTel)  
8. Only then consider deeper ACP/OpenHands UI adaptation
