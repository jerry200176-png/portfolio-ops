"""Deterministic reducer: TaskState is fully rebuildable from events."""

from __future__ import annotations

from .models import AGENT_RUN_EVENTS, Event, TaskState
from .router import ROUTING_TABLE, _failure_signature


def reduce(events: list[Event]) -> TaskState:
    """Fold events left-to-right into TaskState. Pure and deterministic."""
    state = TaskState()
    for event in events:
        state = apply_event(state, event)
    return state


def apply_event(state: TaskState, event: Event) -> TaskState:
    """Apply a single already-validated event. Does not re-check routing."""
    # Copy mutable fields
    new = TaskState(
        task_id=state.task_id or event.task_id,
        current_node=state.current_node,
        task_status=state.task_status,
        retry_count=dict(state.retry_count),
        agent_run_count=state.agent_run_count,
        builder_actor_id=state.builder_actor_id,
        reviewer_actor_id=state.reviewer_actor_id,
        approved_head_sha=state.approved_head_sha,
        blocker=state.blocker,
        repository=state.repository or event.repository,
        base_sha=state.base_sha,
        head_sha=state.head_sha,
        failure_signatures=list(state.failure_signatures),
        human_approved=state.human_approved,
        closed=state.closed,
    )

    if event.base_sha is not None:
        new.base_sha = event.base_sha

    # Head SHA change invalidates prior human approval
    if event.head_sha is not None:
        if new.head_sha is not None and event.head_sha != new.head_sha:
            new.approved_head_sha = None
            new.human_approved = False
        new.head_sha = event.head_sha

    if event.event_type in AGENT_RUN_EVENTS:
        new.agent_run_count += 1

    et = event.event_type

    if et == "TASK_CREATED":
        new.current_node = ROUTING_TABLE[et]
        new.task_status = "investigating"

    elif et == "INVESTIGATION_COMPLETED":
        new.current_node = ROUTING_TABLE[et]
        new.task_status = "building"

    elif et == "BUILD_COMPLETED":
        new.builder_actor_id = event.actor_id
        # New build invalidates prior reviewer decision for a fresh review cycle
        new.reviewer_actor_id = None
        new.current_node = ROUTING_TABLE[et]
        new.task_status = "reviewing"

    elif et == "REVIEW_REJECTED":
        new.reviewer_actor_id = event.actor_id
        node = "builder"
        new.retry_count[node] = new.retry_count.get(node, 0) + 1
        new.current_node = ROUTING_TABLE[et]
        new.task_status = "building"

    elif et == "REVIEW_APPROVED":
        new.reviewer_actor_id = event.actor_id
        new.current_node = ROUTING_TABLE[et]
        new.task_status = "human_approval_required"

    elif et == "HUMAN_APPROVED":
        new.human_approved = True
        new.approved_head_sha = event.head_sha or new.head_sha
        new.current_node = "close"
        new.task_status = "closed_success"
        new.closed = True
        new.blocker = None

    elif et == "HUMAN_REJECTED":
        new.human_approved = False
        new.approved_head_sha = None
        new.current_node = "close"
        new.task_status = "closed_blocked"
        new.closed = True
        new.blocker = "human_rejected"

    elif et == "NODE_FAILED":
        node = event.node
        new.retry_count[node] = new.retry_count.get(node, 0) + 1
        sig = _failure_signature(event)
        if sig:
            new.failure_signatures.append(sig)
        # Stay on same node for retry; status unchanged unless exhausted (validated upstream)
        new.current_node = node

    return new


def can_close_successfully(state: TaskState) -> bool:
    """Security gate: successful close requires human approval of current head."""
    if not state.human_approved:
        return False
    if not state.approved_head_sha:
        return False
    if state.head_sha and state.approved_head_sha != state.head_sha:
        return False
    return state.task_status == "closed_success"
