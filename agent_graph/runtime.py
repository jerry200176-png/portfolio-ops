"""Graph runtime: validate → append → reduce. Dry-run only — no external APIs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from .models import Event, TaskState
from .reducer import can_close_successfully, reduce
from .router import TransitionResult, validate_transition
from .store import AppendOnlyEventStore


@dataclass
class ApplyResult:
    accepted: bool
    duplicate: bool
    state: TaskState
    event: Optional[Event] = None
    reason: Optional[str] = None
    blocker: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "accepted": self.accepted,
            "duplicate": self.duplicate,
            "reason": self.reason,
            "blocker": self.blocker,
            "event_id": self.event.event_id if self.event else None,
            "state": self.state.snapshot(),
        }


class GraphRuntime:
    """Deterministic graph runtime over an append-only event log.

    Restrictions (v0):
    - Does not call Cursor Agents API
    - Does not call GitHub Operator
    - Does not merge or deploy
    - Does not auto-approve an actor's own work
    """

    def __init__(self, store: Optional[AppendOnlyEventStore] = None) -> None:
        self.store = store or AppendOnlyEventStore()

    def state_for(self, task_id: str) -> TaskState:
        return reduce(self.store.for_task(task_id))

    def replay(self, task_id: str) -> TaskState:
        """Rebuild state from events only (same as state_for)."""
        return self.state_for(task_id)

    def apply(self, event: Event) -> ApplyResult:
        """Validate and append an event. Duplicate event_id is idempotent."""
        if self.store.has(event.event_id):
            existing = self.store.get(event.event_id)
            assert existing is not None
            # Idempotent: identical payload is a no-op success; conflicting payload is rejected
            if existing.to_dict() != event.to_dict():
                return ApplyResult(
                    accepted=False,
                    duplicate=True,
                    state=self.state_for(event.task_id),
                    event=existing,
                    reason="duplicate event_id with differing payload",
                )
            return ApplyResult(
                accepted=True,
                duplicate=True,
                state=self.state_for(event.task_id),
                event=existing,
                reason="duplicate event_id (idempotent)",
            )

        state = self.state_for(event.task_id)
        check: TransitionResult = validate_transition(state, event)
        if not check.accepted:
            # Materialize blocker on state for audit visibility without appending
            blocked = TaskState(**{**state.__dict__})
            if check.blocker:
                blocked.blocker = check.blocker
                if check.blocker.startswith("retry_exhausted") or check.blocker.startswith(
                    "duplicate_failure"
                ) or check.blocker == "agent_run_budget_exhausted":
                    blocked.task_status = "blocked"
            return ApplyResult(
                accepted=False,
                duplicate=False,
                state=blocked,
                event=event,
                reason=check.reason,
                blocker=check.blocker,
            )

        # Security: never allow a synthetic "successful close" without human approval path
        if event.event_type == "HUMAN_APPROVED":
            # Will become closed_success only via reducer after this append
            pass

        appended = self.store.append(event)
        if not appended:
            # Race-safe path (shouldn't happen after has() check)
            return ApplyResult(
                accepted=True,
                duplicate=True,
                state=self.state_for(event.task_id),
                event=event,
                reason="duplicate event_id (idempotent)",
            )

        new_state = self.state_for(event.task_id)

        # Post-condition: successful close requires human approval of head
        if new_state.task_status == "closed_success" and not can_close_successfully(new_state):
            # Should be unreachable if router/reducer are correct; fail closed
            raise RuntimeError("invariant violated: closed_success without valid human approval")

        return ApplyResult(
            accepted=True,
            duplicate=False,
            state=new_state,
            event=event,
            reason=None,
            blocker=new_state.blocker,
        )

    def event_trace(self, task_id: str) -> list[dict[str, Any]]:
        return [e.to_dict() for e in self.store.for_task(task_id)]
