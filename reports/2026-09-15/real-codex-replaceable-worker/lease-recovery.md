# Phase 1B — execution lease recovery (crash / orphan)

## Semantics change

| Before | After |
|---|---|
| `lease expiration = takeover allowed` | `lease expiration = reconciliation required` |

Reclaim is allowed only when the previous worker process identity is **confirmed dead**.

## Worker process identity

Bound on the lease after spawn (schema v5):

- `worker_pid`
- `worker_starttime_ticks` (from `/proc/<pid>/stat`)
- `worker_boot_id`
- `worker_pgid` (optional)
- `identity_status`: `pending` → `bound`

PID alone is never enough. `pending` / incomplete / unverifiable identity fail closed.

## Proofs (unittest)

| Case | Result |
|---|---|
| Controller crash + live child + expired TTL | `previous_worker_still_alive`; B not spawned |
| Previous owner confirmed dead | reclaim; fencing token increases; old Attempt `orphaned` |
| Unknown / pending identity | `previous_worker_unverifiable` |
| Incomplete identity (PID only) | fail closed |
| Late result after reclaim | `stale_execution_lease`; no graph transition |

Module: `tests/test_phase1b_lease_recovery.py`
