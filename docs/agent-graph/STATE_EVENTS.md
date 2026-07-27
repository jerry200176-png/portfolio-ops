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

Additional bookkeeping kept in state for enforcement:
`repository`, `base_sha`, `head_sha`, `failure_signatures`,
`human_approved`, `closed`.

## Replay

```text
state_A = reduce(events)
state_B = reduce(events)
assert state_A == state_B
```

`GraphRuntime.replay(task_id)` rebuilds from the append-only log only.

## Evidence rules

Evidence objects must follow `docs/evidence-policy.md`: no secrets, no
credential fragments, primary-source references only. v0 dry-run evidence is
synthetic and labeled as such.
