# Agent Graph Runtime v0

**Status: dry-run only.**

This document describes the minimal deterministic graph runtime added to
`portfolio-ops`. It encodes the human workflow as an append-only event log
with a pure reducer and router.

## Explicitly not connected (v0)

| Capability | Status |
|---|---|
| Cursor Agents API | **Not connected** |
| Cursor Orchestrator / `CURSOR_ORCHESTRATOR_API_KEY` | **Not used** |
| Jerry GitHub Operator | **Not connected** |
| Automatic merge | **Disabled** |
| Automatic deploy | **Disabled** |
| UI dashboard | **Not built** |
| Cross-repository mutation | **Forbidden** |

External agents created by this runtime: **0**. Credential exposure: **NO**.

## Goal

Replace the ad-hoc manual flow with a recoverable, auditable graph:

```
TASK_CREATED
  → INVESTIGATION_COMPLETED
  → BUILD_COMPLETED
  → REVIEW_REJECTED / REVIEW_APPROVED
  → HUMAN_APPROVED / HUMAN_REJECTED
  → GRAPH_STOPPED (when the runtime must stop)
```

## Architecture

```
Event (append-only)
    │
    ▼
AppendOnlyEventStore  ──forbids overwrite / replace──
    │
    ▼
validate_transition (router)  ──budgets, actor isolation, legality──
    │
    ▼
reduce / apply_event (reducer)  ──rebuildable TaskState──
    │
    ▼
GraphRuntime.apply → ApplyResult + current TaskState
```

`GRAPH_STOPPED` is appended when the runtime refuses to continue because of
retry exhaustion, duplicate failure signatures, or total agent-run budget
exhaustion. Because the stop is an event, replay rebuilds the same blocked
state instead of relying on in-memory execution history.

Implementation language: **Python 3** (stdlib only). Package:
`agent_graph/`. No LangGraph, no orchestration framework.

### Nodes

| Node | Role |
|---|---|
| `intake` | Accept `TASK_CREATED` |
| `investigator` | Produce investigation conclusion |
| `builder` | Produce build / repair (new `head_sha`) |
| `reviewer` | Approve or reject build (≠ builder actor) |
| `human_gate` | Founder approval of a specific `head_sha` |
| `close` | Terminal success or blocked |

### Security boundaries (enforced in router)

1. Builder and reviewer **must** be different `actor_id`s.
2. Reviewer **must not** merge (`conclusion=merge` rejected).
3. `BUILD_COMPLETED` **must** carry a non-empty `head_sha`.
4. Successful close **requires** `HUMAN_APPROVED` for the current `head_sha`.
5. `HUMAN_APPROVED` is rejected unless both the event and reduced state carry
   the same non-empty `head_sha`.
6. Changing `head_sha` clears `approved_head_sha` / `human_approved`.
7. Max retries per node = **2**; identical failure signature twice →
   `GRAPH_STOPPED`.
8. Max total agent runs = **6**; exhaustion appends `GRAPH_STOPPED`.
9. Events are **append-only**; duplicate `event_id` is idempotent.

## Package layout

```
agent_graph/
  models.py      # Event, TaskState, limits
  store.py       # AppendOnlyEventStore
  router.py      # validate_transition, ROUTING_TABLE
  reducer.py     # reduce / apply_event
  runtime.py     # GraphRuntime.apply
  dry_run.py     # end-to-end synthetic scenario (no I/O APIs)
tests/
  test_graph_runtime.py
docs/agent-graph/
  GRAPH_RUNTIME_V0.md   (this file)
  STATE_EVENTS.md
  ROUTING_RULES.md
```

## How to run

```bash
# Unit tests
python3 -m unittest tests.test_graph_runtime -v

# Dry-run scenario (prints event trace + final state JSON)
python3 -m agent_graph.dry_run
```

## Relationship to portfolio policy

This runtime does **not** relax `CLAUDE.md`, `governance/AUTONOMY_POLICY.md`,
or `.claude/hooks`. It is a control-plane skeleton for future orchestration.
Any future wiring to real agents must preserve Founder approval for merge,
deploy, secrets, and production data mutation.
