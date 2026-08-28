# State & Events — Agent Graph Runtime v0

**Dry-run runtime only.** Events are not persisted to GitHub or Cursor.
No Cursor API / GitHub Operator / merge / deploy.

## Event (append-only)

Every event contains at least:

| Field | Type | Notes |
|---|---|---|
| `event_id` | string | Globally unique; duplicate id is idempotent |
| `task_id` | string | Task correlation key |
| `timestamp` | string | ISO-8601 UTC |
| `event_type` | string | See table below |
| `node` | string | Emitting node |
| `actor_id` | string | Who emitted the event |
| `actor_role` | string | `system` \| `investigator` \| `builder` \| `reviewer` \| `human` |
| `repository` | string | Target repo (informational in v0) |
| `base_sha` | string \| null | Base commit |
| `head_sha` | string \| null | Current head under consideration |
| `conclusion` | string \| null | Outcome label |
| `evidence` | object \| null | Structured evidence (no secrets) |

Events are **never overwritten**. The store rejects `overwrite` /
`replace_all`. The only way to change observable state is to append a new
event and re-reduce.

## Event types (v0)

| `event_type` | Emitted from | Meaning |
|---|---|---|
| `TASK_CREATED` | `intake` | Task entered the graph |
| `INVESTIGATION_COMPLETED` | `investigator` | Investigation done |
| `BUILD_COMPLETED` | `builder` | Build or repair produced a `head_sha` |
| `REVIEW_REJECTED` | `reviewer` | Review failed; back to builder |
| `REVIEW_APPROVED` | `reviewer` | Review passed; await human |
| `HUMAN_APPROVED` | `human_gate` | Founder approved a specific `head_sha` |
| `HUMAN_REJECTED` | `human_gate` | Founder rejected; close blocked |
| `NODE_FAILED` | agent node | Failure / retry accounting |
| `GRAPH_STOPPED` | runtime / `system` | Persisted stop caused by retry exhaustion, duplicate failure, or run-budget exhaustion |

`BUILD_COMPLETED` must always carry a non-empty `head_sha`. `HUMAN_APPROVED`
must also carry a non-empty `head_sha`, and that value must exactly match the
task's current reduced `head_sha`.

### `GRAPH_STOPPED` evidence payload

`GRAPH_STOPPED` stores the stop condition in append-only form so replay can
rebuild a blocked task without consulting execution memory. The event evidence
contains at least:

- `reason`
- `blocker`
- `failure_signature` (when applicable)
- `retry_count`
- `agent_run_count`
- `trigger_event_id`
- `trigger_event_type`

## Reduced state

`reduce(events) → TaskState` is pure and deterministic. Fields:

| Field | Meaning |
|---|---|
| `current_node` | Active graph node |
| `task_status` | `pending` / `investigating` / `building` / `reviewing` / `human_approval_required` / `closed_success` / `closed_blocked` / `blocked` |
| `retry_count` | Per-node failure/reject counters |
| `agent_run_count` | Total agent-facing events applied |
| `builder_actor_id` | Last builder actor |
| `reviewer_actor_id` | Last reviewer actor |
| `approved_head_sha` | Head SHA approved by a human (if any) |
| `blocker` | Machine-readable stop reason (if any) |
| `stopped` | Whether replay has reduced a persisted `GRAPH_STOPPED` |

Additional bookkeeping kept in state for enforcement:
`repository`, `base_sha`, `head_sha`, `failure_signatures`,
`human_approved`, `closed`.

## Replay

```text
state_A = reduce(events)
state_B = reduce(events)
assert state_A == state_B
```

`GraphRuntime.replay(task_id)` rebuilds from the append-only log only,
including any `GRAPH_STOPPED` event.

## Evidence rules

Evidence objects must follow `docs/evidence-policy.md`: no secrets, no
credential fragments, primary-source references only. v0 dry-run evidence is
synthetic and labeled as such.
