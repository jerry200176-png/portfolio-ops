# ENGINEERING_OS_DISCOVERY V1

**Nature:** read-only architecture / autonomy-gap audit  
**Date:** 2026-09-18  
**Worktree:** `/home/jerry/workspace/tasks/portfolio-ops/engineering-os-discovery-v1`  
**Base tip:** `5479119` (`origin/main` at session start)  
**Supersedes (partially):** `docs/audits/agent-company-control-plane-v1` claims that live AllTrue `harness.sqlite` was still schema v1 — **now schema v4 / domain_authority** (cutover 2026-09-17).

| Artifact | Purpose |
|---|---|
| [SYSTEM_TOPOLOGY.md](./SYSTEM_TOPOLOGY.md) | Actual components + control/data flows |
| [CAPABILITY_MATRIX.md](./CAPABILITY_MATRIX.md) | Capability classification with maturity labels |
| [AUTHORITY_MAP.md](./AUTHORITY_MAP.md) | Canonical authority / projection / writer / reconcile |
| [MANUAL_INTERVENTION_MAP.md](./MANUAL_INTERVENTION_MAP.md) | Where Founder still must intervene |
| [TARGET_GAP_GRAPH.md](./TARGET_GAP_GRAPH.md) | Smallest dependency graph to Goal→autonomous loop |
| [NEXT_5_BOUNDED_GOALS.md](./NEXT_5_BOUNDED_GOALS.md) | Ordered next engineering Goals |
| [OPEN_SWE_REUSE_SPIKE.md](./OPEN_SWE_REUSE_SPIKE.md) | Open SWE / OSS reuse spike (2026-09-18) |
| [AUDIT_RESULT.json](./AUDIT_RESULT.json) | Machine-readable verdict |

**GitHub role:** durable research/evidence only.  
**Runtime Goal authority** (deferred `H4B_E2E_AUTONOMY_ACCEPTANCE`, status `BLOCKED_EXTERNAL_CAPACITY`) remains under host `/home/jerry/workspace/state/alltrue/goals/harness/H4B-E2E/GOAL.json` — not mirrored as executable state in this package.

**Non-goals of this package:** new framework, new DB, production config changes, governance abstraction sprawl, remediations beyond documenting security findings, starting H4B.

**Primary metric:** remove Founder intervention while keeping deterministic safety boundaries and verifiable evidence.
