# Routing Rules — Agent Graph Runtime v0

**Dry-run runtime only.** These rules are enforced in `agent_graph/router.py`.
Cursor Agents API, GitHub Operator, auto-merge, and deploy are **not** wired.

## Happy-path routing

| Event | Next node |
|---|---|
| `TASK_CREATED` | `investigator` |
| `INVESTIGATION_COMPLETED` | `builder` |
| `BUILD_COMPLETED` | `reviewer` |
| `REVIEW_REJECTED` | `builder` |
| `REVIEW_APPROVED` | `human_gate` |
| `HUMAN_APPROVED` | `close` (status=`closed_success`) |
| `HUMAN_REJECTED` | `close` (status=`closed_blocked`) |
| `NODE_FAILED` | same node (retry), unless exhausted |

## Legal `current_node` before each event

| Event | Allowed `current_node` |
|---|---|
| `TASK_CREATED` | `None`, `intake` |
| `INVESTIGATION_COMPLETED` | `investigator` |
| `BUILD_COMPLETED` | `builder` |
| `REVIEW_REJECTED` / `REVIEW_APPROVED` | `reviewer` |
| `HUMAN_APPROVED` / `HUMAN_REJECTED` | `human_gate` |
| `NODE_FAILED` | `investigator`, `builder`, `reviewer` |

Any other combination is an **illegal transition** and is rejected without
appending.

## Actor isolation

- The same `actor_id` **must not** be both builder and reviewer for a task.
- `REVIEW_APPROVED` / `REVIEW_REJECTED` with `actor_id == builder_actor_id`
  → rejected (`blocker=builder_reviewer_same_actor`).
- Reviewer `conclusion=merge` → rejected (`blocker=reviewer_merge_forbidden`).
- Reviewer does **not** merge in v0 (or any future auto path without Founder).

## Human gate

- Only `actor_role=human` may emit `HUMAN_APPROVED` / `HUMAN_REJECTED`.
- `HUMAN_APPROVED` requires `head_sha` equal to the task's current `head_sha`.
- Successful close (`closed_success`) is impossible without a matching human
  approval of the current head.
- `HUMAN_REJECTED` closes as `closed_blocked`.

## Head SHA invalidation

When a new event carries a different `head_sha` than the reduced state:

1. `approved_head_sha` is cleared.
2. `human_approved` is set to `false`.
3. Prior human approval of the old SHA cannot close the new head.

## Budgets & failure stops

| Limit | Value | Effect |
|---|---|---|
| Max retries per node | `2` | Further `NODE_FAILED` on that node → `retry_exhausted:<node>` |
| Identical failure signature | 2nd time | → `duplicate_failure:<sig>` |
| Max total agent runs | `6` | Further agent events → `agent_run_budget_exhausted` |

Agent-run-counted event types:
`INVESTIGATION_COMPLETED`, `BUILD_COMPLETED`, `REVIEW_REJECTED`,
`REVIEW_APPROVED`, `NODE_FAILED`.

There is **no** infinite retry. There is **no** self-approval path.

## Idempotency

Re-applying an event with the same `event_id` and identical payload succeeds
as a no-op (`duplicate=true`). A same `event_id` with a different payload is
rejected.
