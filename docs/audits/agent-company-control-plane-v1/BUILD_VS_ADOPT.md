# BUILD_VS_ADOPT

**Audit:** `AGENT_COMPANY_CONTROL_PLANE_AUDIT_V1` · 2026-09-17  
Decisions challenge sunk cost. Options: KEEP | HARDEN | ADOPT_EXTERNAL | ADAPT_EXTERNAL | REPLACE | DELETE | DEFER.

---

## Subsystem decisions

| Subsystem | Decision | Rationale | Cost if wrong |
|-----------|----------|-----------|---------------|
| AllTrue `scripts/harness` (Goal/Plan/Dispatch/WorkerRun/leases/fencing) | **HARDEN** | AllTrue-specific authority + autonomy_gate binding; already MERGED H0–H4b | Abandon → rebuild product fences in foreign system |
| Live `harness.sqlite` cutover to schema v4 | **HARDEN (P0)** | Code/runtime split is fake automation | Continue JSON SoT forever |
| `state/alltrue/*.json` as authority | **REPLACE** (demote to projections/debug) | Competing SoT | Dual-write bugs |
| portfolio-ops `agent_graph` as second control plane | **DEFER enablement; ADAPT selective modules** | Event store/adapters valuable; dual scheduler harmful | Two truth systems |
| `graph-scheduler.service` | **DELETE or park disabled with doc** | Present but inactive — false sense of automation | Accidental dual dispatch |
| agent-control worktrees/sessions | **KEEP** | Proven isolation; SWE-ReX-class problem already solved simply | K8s sandbox cosplay |
| Restate for ExternalEvent→wake | **ADAPT_EXTERNAL** (after Gate-1) | PoC proved awakeable wake; don't replace fencing | Ops complexity if adopted as whole CP |
| Temporal | **DEFER** | Solves same class as Restate; heavier cluster for 1–2 operator machines | Ops burden > benefit |
| LangGraph as company OS | **DELETE (as strategy)** | Wrong layer; graph overengineering risk already observed | Endless node/edge theater |
| OpenHands full platform replace | **DEFER / ADAPT UI ideas only** | Canvas UI split useful; replacing harness loses deploy/policy DNA | Migration sink |
| SWE-ReX | **DEFER** | Learn isolation patterns; agent-control sufficient | Extra runtime |
| MCP | **KEEP/ADAPT** as tool protocol | Already ecosystem-standard | — |
| ACP | **DEFER** deep integration | Useful if IDE-first workers expand | Premature |
| A2A | **DEFER** | Multi-agent protocol before single WorkItem SoT is cosplay | — |
| Langfuse / OTel GenAI | **ADAPT later (P2)** | Need cost/quality telemetry after autonomy loop works | Observability without control |
| k8s agent-sandbox / Nomad / K8s fleet | **DELETE from near-term plan** | 3 roles; no cluster need | Cosplay |
| exo receipts/locks | **KEEP** for repo governance | Orthogonal to WorkerRun | — |
| engineering-intelligence “control” claims | **KEEP as research only** | Must not pretend to wake workers | False automation |
| Founder Console | **ADAPT** Restate UI + custom boards (per UI spike) | Plan-only; implement after SoT | UI over empty store |
| CAO / cli-agent-orchestrator binaries | **DELETE or ignore** | Competing unused orchestrator | Confusion |
| In-App BugReport product | **KEEP** product; **HARDEN** CP adapter | Don't rebuild bug UI in harness | — |

---

## Challenge questions (answers)

**Are we rebuilding solved distributed-systems problems?**  
Partially — durable wake/crash recovery yes (Restate/Temporal). Product fencing, exact-SHA deploy, autonomy_gate, school-PII boundaries — **no**, those are AllTrue-specific.

**Is custom code providing AllTrue-specific value?**  
Yes for harness contracts + deploy evidence + policy. No for a second event-sourced scheduler that isn't running.

**Would Restate/Temporal/OpenHands/SWE-ReX remove maintenance?**  
Restate: yes for wake/inbox. Temporal: maybe, higher ops. OpenHands/SWE-ReX: isolation already covered; platform replace would **increase** migration cost.

**Would adopting create more complexity than it removes?**  
Full Temporal/K8s/OpenHands-replace: **yes**. Bounded Restate adapter: **no** if Gate-1 passes and AllTrue remains authority for leases/permissions.

**Copying big-company architecture without scale?**  
Risk areas: fairness/capacity schedulers, multi-cluster sandbox, full replay platforms, A2A mesh, dual graph engines. **Do not build.**

---

## Recommended posture (6–12 months)

1. **One authority store:** AllTrue harness SQLite (v4+) as WorkItem/WorkerRun SoT.  
2. **One durable wake spine:** Restate adapter (ADAPT) for external events — not for policy.  
3. **One isolation gateway:** agent-control.  
4. **Steal adapters, not platforms:** reuse agent_graph GitHub/deploy observe code.  
5. **UI last among P0s:** Console on real projections, not ahead of SoT.
