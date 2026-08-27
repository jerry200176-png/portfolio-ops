# AllTrue cross-date reschedule calendar proposal — 2026-08-27

## Finding

Issue [#2002](https://github.com/jerry200176-png/AllTrue_System/issues/2002)
describes a real operational failure mode: a cross-date reschedule can leave a
`schedules.status=scheduled` destination that occupies the teacher's
availability while its corresponding `ClassSession` is absent, so the teacher
calendar renders a false free slot.

The current code makes the boundary explicit but incomplete:

- `ClassSessionController::autoMaterializeScheduledExceptionsForRange()` only
  repairs same-day reads.
- `ScheduleController::ensureClassSessionForScheduleData()` intentionally
  skips a cross-date `original_schedule_id` chain because creating a second
  row before the atomic move can create a duplicate ghost.
- The calendar loads the `ClassSession` projection and `schedules` exceptions
  separately, then merges them. Availability can therefore know about a
  schedule row that the calendar cannot display.

This is a read-model and transaction-contract problem, not a safe candidate for
blind production data correction.

## Recommended contract

1. Keep `ClassSession` authoritative for attendance, evaluation, and billing.
2. Make the calendar projection completeness-safe for a valid, non-stale
   cross-date rescheduled target by returning a clearly marked,
   schedule-backed projected occurrence (`isProjected=true`, source schedule
   id, and no ClassSession id). This read path must not write production data.
3. Keep schedule-backed projected occurrences busy in availability and merge
   them by the same course/date/start slot so a later materialized row replaces
   the projection exactly once.
4. Make the reschedule mutation path atomic and idempotent: the schedule pair,
   the moved ClassSession, and any linked learning/attendance records must
   either complete together or return an actionable error. Ambiguous or stale
   chains must be surfaced for review, never silently duplicated.

The projection is the safe immediate consistency layer; the mutation path is
the long-term repair. Automatically materializing an ambiguous cross-date row
on a GET is not recommended.

## Regression matrix before implementation

- A valid cross-date target with no destination ClassSession appears exactly
  once in the teacher calendar and remains busy in availability.
- After the atomic move creates the ClassSession, the projected occurrence is
  replaced by the materialized occurrence without duplication.
- A stale/superseded scheduled row is hidden according to the existing stale
  exception rules and does not occupy the slot.
- A `type=extra` makeup schedule remains schedule-only and busy under the
  existing R13 contract.
- A duplicate reschedule chain returns one deterministic occurrence and an
  audit signal; it never creates a second attendance-bearing row.
- Branch and teacher authorization filters apply equally to materialized and
  projected rows.

## Release and safety gates

Implementation requires an isolated PR with backend feature tests, calendar
merge tests, a read-only production-shaped reproduction, and post-deploy
calendar/availability verification. No production data repair, migration, or
read-side materialization should run until the Founder approves the contract
and rollback plan.

Rollback is a code revert through the normal deployment workflow; the proposed
read projection has no schema or data migration.
