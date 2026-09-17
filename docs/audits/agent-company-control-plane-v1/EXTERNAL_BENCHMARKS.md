# EXTERNAL_BENCHMARKS

**Audit:** `AGENT_COMPANY_CONTROL_PLANE_AUDIT_V1` · Research date: 2026-09-17  
Method: official docs + GitHub releases/source. Rubric: STRONG | PARTIAL | ABSENT | UNKNOWN.

---

## Capability snapshot

| System | Durable ID | Crash recovery | Leases | Worker abs. | Workspace isol. | Event ingest | Human approval | Observability |
|--------|------------|----------------|--------|-------------|-----------------|--------------|----------------|---------------|
| OpenHands Canvas/SDK | PARTIAL | PARTIAL | ABSENT/UNKNOWN | PARTIAL | STRONG | PARTIAL | PARTIAL | PARTIAL |
| SWE-agent / SWE-ReX | ABSENT | PARTIAL | ABSENT | STRONG | STRONG | ABSENT | ABSENT | PARTIAL |
| Restate | STRONG | STRONG | PARTIAL (per-key) | STRONG | ABSENT | STRONG | STRONG | STRONG |
| Temporal | STRONG | STRONG | STRONG | STRONG | ABSENT | STRONG | STRONG | STRONG |
| LangGraph | STRONG (thread) | PARTIAL→STRONG* | ABSENT | PARTIAL | ABSENT | PARTIAL | STRONG | PARTIAL |
| Pydantic AI/graph | PARTIAL† | PARTIAL† | ABSENT | PARTIAL | ABSENT | PARTIAL | PARTIAL | PARTIAL |
| MCP | PARTIAL (Tasks) | PARTIAL | ABSENT | ABSENT | PARTIAL (roots) | PARTIAL | PARTIAL | PARTIAL |
| A2A | STRONG | PARTIAL | ABSENT | ABSENT | ABSENT | STRONG | STRONG | PARTIAL |
| ACP | PARTIAL | PARTIAL | ABSENT | ABSENT | PARTIAL | PARTIAL | STRONG | PARTIAL |
| OTel GenAI | N/A | N/A | N/A | N/A | N/A | N/A | N/A | STRONG (conv.) |
| Langfuse | N/A | N/A | N/A | N/A | N/A | N/A | N/A | STRONG |
| k8s agent-sandbox | PARTIAL | PARTIAL | ABSENT | PARTIAL | STRONG | ABSENT | ABSENT | PARTIAL |

\*Needs durable checkpointer. †Strong when TemporalDurability wraps agent.

---

## 1. OpenHands / Agent Canvas / software-agent-sdk

| Artifact | URL | Version / date |
|----------|-----|----------------|
| Canvas architecture | https://docs.openhands.dev/openhands/usage/agent-canvas/architecture | live 2026-09-17 |
| SDK overview | https://docs.openhands.dev/sdk/arch/overview | live |
| software-agent-sdk | https://github.com/OpenHands/software-agent-sdk | **v1.49.1** (2026-09-17) |
| OpenHands | https://github.com/OpenHands/OpenHands | **v1.20.0** (2026-09-17) |

**Teachings for Founder UI:** Canvas is a **client of backends**, not the runtime. Split Agent Server (conversations/tools) vs Automation Server (schedules/triggers) vs workspace (isolation). Multi-backend selector is first-class. State lives on backends; UI stores connections.

**Not a substitute for:** durable company-wide WorkItem authority, production deploy fencing, AllTrue policy.

---

## 2. SWE-agent / SWE-ReX

| Artifact | URL | Version |
|----------|-----|---------|
| SWE-ReX | https://github.com/SWE-agent/SWE-ReX | **v1.4.0** (2025-08-14) |
| Architecture | https://swe-rex.com/latest/architecture/ | live |
| SWE-agent | https://github.com/SWE-agent/SWE-agent | **v1.1.0** (2025-05-22) |

**Teaching:** Disentangle **agent logic** from **execution runtime** (Deployment → RemoteRuntime → sandbox). Strong isolation/worker abstraction; **ABSENT** company control plane (leases, intake, deploy).

---

## 3. Restate

| Artifact | URL | Version |
|----------|-----|---------|
| Services / VO / Workflow | https://docs.restate.dev/foundations/services | live |
| Awakeables / signals | https://docs.restate.dev/develop/ts/external-events | live |
| Releases | https://github.com/restatedev/restate | **v1.7.10** (2026-09-14) |

**Fit:** ExternalEvent → durable wake; human approvals via signals/awakeables; journaled crash recovery. **Not** a code sandbox. Matches local AllTrue PoC verdict `ADOPT_RESTATE_SPINE` for wake spine only.

---

## 4. Temporal

| Artifact | URL | Version |
|----------|-----|---------|
| Workers / Workflow IDs | https://docs.temporal.io/workers · workflowid-runid | live |
| Signals / Updates | https://docs.temporal.io/handling-messages | live |
| Server | https://github.com/temporalio/temporal | **v1.32.0** (2026-09-11) |

**Fit:** Mature durable orchestration, task-queue leases, activity heartbeats. Heavier ops footprint than Restate single-binary for this fleet size. Prefer only if multi-tenant workflow platform needs exceed Restate+AllTrue fencing.

---

## 5. LangGraph / Pydantic AI

| Artifact | URL | Version |
|----------|-----|---------|
| LangGraph checkpointers/interrupts | https://docs.langchain.com/oss/python/langgraph/ | langgraph **1.2.11** (2026-08-11) |
| pydantic-graph | https://ai.pydantic.dev/graph/ | live |
| Pydantic AI + Temporal | https://ai.pydantic.dev/durable_execution/temporal/ | pydantic-ai **v2.44.0** |

**Teaching:** Graphs excel at **LLM state machines + HITL interrupts**. They are **not** replacements for lease/CAS/deploy authority. Using LangGraph as the company control plane would be category error / big-company cosplay at current scale.

---

## 6. MCP / A2A / ACP

| Spec | URL | Note |
|------|-----|------|
| MCP | https://modelcontextprotocol.io/specification/2026-07-28 | Latest tag; Tasks as extension; tool/context plug-in |
| MCP 2025-11-25 | https://modelcontextprotocol.io/specification/2025-11-25 | Still widely referenced (Sampling/Roots/Elicitation) |
| A2A 1.0 | https://a2a-protocol.org/latest/specification/ | Agent↔agent Task lifecycle |
| ACP | https://agentclientprotocol.com/ · schema-v1.21.0 (2026-08-20) | Editor↔coding-agent wire protocol |

**Harness relevance:** MCP for tools; ACP for IDE-agent interoperability (OpenHands Canvas already supports ACP agents); A2A for future multi-agent handoff — **none** replace WorkerRun/leases.

---

## 7. Observability

| System | URL | Version |
|--------|-----|---------|
| OTel GenAI conventions | https://github.com/open-telemetry/semantic-conventions-genai | Development status; core moved GenAI out |
| Langfuse | https://langfuse.com/docs · https://github.com/langfuse/langfuse | **v4.37.0** (2026-09-16) |

Instrument model/tool/cost traces; do not confuse with orchestration.

---

## 8. kubernetes-sigs/agent-sandbox (benchmark only)

https://github.com/kubernetes-sigs/agent-sandbox **v1.0.2** (2026-09-11) — strong K8s sandbox CRD. **Do not adopt** at current 3-role fleet; agent-control worktrees + Docker staging suffice.

---

## Pattern triangulation

| Concern | Best external reference |
|---------|-------------------------|
| Founder UI vs runtime split | OpenHands Agent Canvas |
| Code sandbox harness | SWE-ReX / OpenHands workspaces |
| Durable wake / approvals | Restate (or Temporal) |
| LLM graph + HITL | LangGraph interrupts |
| IDE agent wire | ACP |
| Agent↔agent | A2A |
| Tool plug-in | MCP |
| Telemetry product | Langfuse + OTel GenAI attrs |

**Unknowns:** OpenHands Enterprise lease/audit internals; MCP client migration to 2026-07-28; A2A server durability implementation-defined; Restate vs Temporal vendor comparison pages are vendor-authored.
