# CAPABILITY_MATRIX

**Audit:** `AGENT_COMPANY_CONTROL_PLANE_AUDIT_V1` · 2026-09-17  
Values: STRONG | PARTIAL | PLAN_ONLY | POC_ONLY | ABSENT | UNKNOWN  
CURRENT_ALLTRUE = evidence from this workspace (code+runtime), not aspirational docs.

| Capability | CURRENT_ALLTRUE | OPENHANDS | SWE_AGENT/SWE_REX | RESTATE | TEMPORAL | LANGGRAPH/PYDANTIC | OTHER | GAP | RECOMMENDATION |
|------------|-----------------|-----------|-------------------|---------|----------|--------------------|-------|-----|----------------|
| durable task identity | PARTIAL (WorkerRun MERGED; live DB v1) | PARTIAL | ABSENT | STRONG | STRONG | STRONG* | A2A STRONG | Live cutover | HARDEN harness store |
| append-only event history | PARTIAL (agent_graph dogfood only) | PARTIAL | ABSENT | STRONG | STRONG | PARTIAL | — | Unify | ADOPT Restate journal *or* keep one SQLite events table |
| materialized state | PARTIAL (JSON flood + dual SQLite) | PARTIAL | ABSENT | STRONG | STRONG | STRONG | — | Single projection | HARDEN |
| deterministic replay | ABSENT (AllTrue live) | ABSENT | ABSENT | STRONG | STRONG | PARTIAL | — | Only where needed | DEFER full replay; ADOPT for wake path |
| crash recovery | PARTIAL (worktree survives; loop doesn't) | PARTIAL | PARTIAL | STRONG | STRONG | PARTIAL | — | Supervisor durability | ADOPT Restate for waits |
| resume/adopt | PARTIAL (agent-start --attach RUNTIME) | PARTIAL | PARTIAL | STRONG | STRONG | STRONG | ACP PARTIAL | Wire to WorkerRun | HARDEN |
| retry policy | PARTIAL (manual/CI) | PARTIAL | PARTIAL | STRONG | STRONG | PARTIAL | — | Codify | HARDEN deterministic |
| idempotency | PARTIAL (CAS code; PoC event_id) | UNKNOWN | ABSENT | STRONG | STRONG | PARTIAL | — | Live ingest | HARDEN+ADAPT Restate |
| exactly-once / effectively-once side effects | PARTIAL (deploy exact-SHA; else weak) | ABSENT | ABSENT | STRONG | STRONG | ABSENT | — | Fence side effects | KEEP AllTrue fencing |
| distributed lease | PARTIAL (code; weak live) | ABSENT | ABSENT | PARTIAL | STRONG | ABSENT | exo PARTIAL | Use live | HARDEN AllTrue leases |
| fencing token | PARTIAL→STRONG design; weak live | ABSENT | ABSENT | PARTIAL | PARTIAL | ABSENT | exo | Bind every attach | HARDEN |
| scheduling | PARTIAL (JSON lanes; graph sched disabled) | PARTIAL | ABSENT | STRONG | STRONG | PARTIAL | — | Simple tick | HARDEN harness reconciler; don't enable dual schedulers |
| resource-aware scheduling | ABSENT | PARTIAL | PARTIAL | PARTIAL | PARTIAL | ABSENT | — | Daan mem gate only | DEFER |
| priority | PARTIAL (convention) | PARTIAL | ABSENT | PARTIAL | STRONG | PARTIAL | — | WorkItem priority | HARDEN |
| fairness | ABSENT | ABSENT | ABSENT | PARTIAL | PARTIAL | ABSENT | — | Not needed | DEFER |
| cancellation | PARTIAL | PARTIAL | PARTIAL | STRONG | STRONG | PARTIAL | — | Cancel WorkItem | HARDEN |
| pause/resume | PARTIAL | PARTIAL | PARTIAL | STRONG | STRONG | STRONG | — | — | HARDEN |
| human approval | PARTIAL (FOUNDER_INBOX JSON) | PARTIAL | ABSENT | STRONG | STRONG | STRONG | ACP STRONG | Console | HARDEN+UI |
| timeout | PARTIAL | PARTIAL | PARTIAL | STRONG | STRONG | PARTIAL | — | Stall detector | HARDEN |
| external event inbox | POC_ONLY (Restate) / ABSENT prod | PARTIAL | ABSENT | STRONG | STRONG | PARTIAL | — | **P0** | ADOPT Restate adapter |
| webhook ingestion | ABSENT CP | PARTIAL | ABSENT | STRONG | STRONG | ABSENT | — | CI/GitHub | ADAPT |
| CI event ingestion | ABSENT auto | PARTIAL | ABSENT | STRONG | STRONG | ABSENT | Actions | **P0** | ADOPT/ADAPT |
| GitHub issue ingestion | PARTIAL (manual) | PARTIAL | ABSENT | ABSENT | ABSENT | ABSENT | gh | Intake | HARDEN adapter |
| In-App feedback ingestion | ABSENT CP (product BugReport exists) | ABSENT | ABSENT | ABSENT | ABSENT | ABSENT | — | Bridge | HARDEN adapter |
| deduplication | PARTIAL (escalation dedupe keys) | PARTIAL | ABSENT | STRONG | STRONG | PARTIAL | — | Intake dedup | HARDEN |
| planning | PARTIAL (H3 MERGED; uneven use) | PARTIAL | PARTIAL | ABSENT | ABSENT | STRONG | — | Keep LLM planner | KEEP harness planner |
| dependency graph | PARTIAL | PARTIAL | ABSENT | PARTIAL | STRONG | STRONG | — | Light deps | HARDEN minimal |
| agent routing | PARTIAL (A/B/C lanes) | PARTIAL | ABSENT | ABSENT | PARTIAL | PARTIAL | — | Capability labels | HARDEN |
| worker abstraction | PARTIAL | PARTIAL | STRONG | STRONG | STRONG | PARTIAL | ACP | Replaceable workers | HARDEN |
| agent interoperability | PARTIAL (multi CLI) | STRONG (ACP) | PARTIAL | ABSENT | ABSENT | PARTIAL | MCP/A2A/ACP | Optional ACP later | DEFER ACP deep |
| workspace isolation | STRONG (worktrees) | STRONG | STRONG | ABSENT | ABSENT | ABSENT | k8s sandbox | Enough | KEEP agent-control |
| secrets | PARTIAL (GH Environments; no Pi secrets on WSL) | PARTIAL | PARTIAL | PARTIAL | PARTIAL | ABSENT | — | Keep fences | KEEP |
| permissions | STRONG (autonomy_gate T/R) | PARTIAL | ABSENT | ABSENT | ABSENT | ABSENT | exo | — | KEEP |
| policy enforcement | STRONG (CI+gate) | PARTIAL | ABSENT | ABSENT | ABSENT | ABSENT | — | — | KEEP |
| budget / token accounting | ABSENT | PARTIAL | ABSENT | ABSENT | ABSENT | PARTIAL | Langfuse | P2 | ADAPT Langfuse later |
| branch lifecycle | PARTIAL | PARTIAL | ABSENT | ABSENT | ABSENT | ABSENT | — | Reconcile | HARDEN |
| worktree lifecycle | PARTIAL (start strong; GC weak) | PARTIAL | PARTIAL | ABSENT | ABSENT | ABSENT | — | GC | HARDEN |
| PR lifecycle | PARTIAL (observe+manual) | PARTIAL | ABSENT | ABSENT | ABSENT | ABSENT | agent_graph adapters | Wire | HARDEN/ADAPT |
| stale-resource GC | PARTIAL | PARTIAL | PARTIAL | ABSENT | ABSENT | ABSENT | — | Automate | HARDEN |
| CI verification | STRONG | PARTIAL | PARTIAL | ABSENT | ABSENT | ABSENT | Actions | — | KEEP |
| staging promotion | PARTIAL (Daan Founder-interactive) | ABSENT | ABSENT | ABSENT | ABSENT | ABSENT | — | Stabilize then automate | HARDEN Daan |
| production activation | STRONG (Environment + exact-SHA) | ABSENT | ABSENT | ABSENT | ABSENT | ABSENT | — | — | KEEP |
| exact-SHA runtime verification | STRONG (version/deployment.json) | ABSENT | ABSENT | ABSENT | ABSENT | ABSENT | wait-github-deploy | — | KEEP |
| rollback | PARTIAL (redeploy prior SHA) | ABSENT | ABSENT | PARTIAL | PARTIAL | ABSENT | — | Runbook | HARDEN docs/automation |
| operational acceptance | PARTIAL (discipline practiced) | ABSENT | ABSENT | ABSENT | ABSENT | ABSENT | — | Encode states | HARDEN |
| user notification | ABSENT CP | PARTIAL | ABSENT | PARTIAL | PARTIAL | ABSENT | — | Later | DEFER |
| audit trail | PARTIAL (transitions table; JSON) | PARTIAL | PARTIAL | STRONG | STRONG | PARTIAL | — | Unify | HARDEN |
| trace / logs | PARTIAL | PARTIAL | PARTIAL | STRONG | STRONG | PARTIAL | OTel | P2 | ADAPT |
| cost telemetry | ABSENT | PARTIAL | ABSENT | ABSENT | ABSENT | PARTIAL | Langfuse | P2 | ADAPT |
| quality/eval telemetry | ABSENT | PARTIAL | PARTIAL | ABSENT | ABSENT | PARTIAL | Langfuse | P2 | DEFER |
| post-run learning | ABSENT | PARTIAL | PARTIAL | ABSENT | ABSENT | PARTIAL | EI research | P2 | DEFER closed loop |
| control-plane UI | PLAN_ONLY | STRONG (Canvas) | ABSENT | STRONG (UI) | STRONG (UI) | PARTIAL | — | Founder Console | ADAPT Restate UI + custom boards |
| multi-machine execution | PARTIAL (roles split; no fleet registry) | PARTIAL | PARTIAL | STRONG | STRONG | ABSENT | — | Labels not K8s | HARDEN simple registry |
| node health | PARTIAL (Pi health WF; Daan mem) | PARTIAL | PARTIAL | PARTIAL | STRONG | ABSENT | — | Heartbeats | HARDEN light |
| capacity management | ABSENT | PARTIAL | PARTIAL | PARTIAL | PARTIAL | ABSENT | — | Cosplay risk | DEFER |
| disaster recovery | PARTIAL (Pi backups scripts) | UNKNOWN | ABSENT | PARTIAL | STRONG | ABSENT | — | Document | HARDEN runbooks |

\*LangGraph thread/checkpoint durability ≠ company WorkItem authority.
