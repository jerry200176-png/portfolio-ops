"""Deterministic router: legal transitions, budgets, and actor isolation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .models import (
    AGENT_RUN_EVENTS,
    EVENT_TYPES,
    MAX_RETRIES_PER_NODE,
    MAX_TOTAL_AGENT_RUNS,
    NODES,
    ACTOR_ROLES,
    Event,
    TaskState,
)

# event_type → next node after a successful apply
ROUTING_TABLE: dict[str, str] = {
    "TASK_CREATED": "investigator",
    "INVESTIGATION_COMPLETED": "builder",
    "BUILD_COMPLETED": "reviewer",
    "REVIEW_REJECTED": "builder",
    "REVIEW_APPROVED": "human_gate",
    "HUMAN_APPROVED": "close",
    "HUMAN_REJECTED": "close",
    # NODE_FAILED stays on the same node (retry) unless exhausted — handled specially
    "GRAPH_STOPPED": "close",
}

# Which current_node values may accept each event_type
ALLOWED_FROM: dict[str, frozenset[Optional[str]]] = {
    "TASK_CREATED": frozenset({None, "intake"}),
    "INVESTIGATION_COMPLETED": frozenset({"investigator"}),
    "BUILD_COMPLETED": frozenset({"builder"}),
    "REVIEW_REJECTED": frozenset({"reviewer"}),
    "REVIEW_APPROVED": frozenset({"reviewer"}),
    "HUMAN_APPROVED": frozenset({"human_gate"}),
    "HUMAN_REJECTED": frozenset({"human_gate"}),
    "NODE_FAILED": frozenset({"investigator", "builder", "reviewer"}),
    "GRAPH_STOPPED": frozenset({"investigator", "builder", "reviewer", "human_gate"}),
}

# Expected emitting node for each event (must match event.node)
EXPECTED_NODE: dict[str, str] = {
    "TASK_CREATED": "intake",
    "INVESTIGATION_COMPLETED": "investigator",
    "BUILD_COMPLETED": "builder",
    "REVIEW_REJECTED": "reviewer",
    "REVIEW_APPROVED": "reviewer",
    "HUMAN_APPROVED": "human_gate",
    "HUMAN_REJECTED": "human_gate",
}


@dataclass(frozen=True)
class TransitionResult:
    accepted: bool
    next_node: Optional[str] = None
    reason: Optional[str] = None
    blocker: Optional[str] = None


def route(event_type: str) -> Optional[str]:
    """Pure routing lookup. NODE_FAILED has no fixed next node."""
    return ROUTING_TABLE.get(event_type)


def validate_transition(state: TaskState, event: Event) -> TransitionResult:
    """Validate whether `event` may be applied to `state`. Deterministic."""

    if event.event_type not in EVENT_TYPES:
        return TransitionResult(False, reason=f"unknown event_type: {event.event_type}")

    if event.node not in NODES:
        return TransitionResult(False, reason=f"unknown node: {event.node}")

    if event.actor_role not in ACTOR_ROLES:
        return TransitionResult(False, reason=f"unknown actor_role: {event.actor_role}")

    if state.closed:
        return TransitionResult(False, reason="task already closed")

    if state.stopped and event.event_type != "GRAPH_STOPPED":
        return TransitionResult(False, reason=f"task blocked: {state.blocker}", blocker=state.blocker)

    if state.blocker and event.event_type != "TASK_CREATED":
        # Blocked tasks reject further progress events (except duplicate handled upstream)
        return TransitionResult(False, reason=f"task blocked: {state.blocker}", blocker=state.blocker)

    if state.task_id is not None and event.task_id != state.task_id:
        return TransitionResult(False, reason="task_id mismatch")

    expected = EXPECTED_NODE.get(event.event_type)
    if expected and event.node != expected:
        return TransitionResult(
            False,
            reason=f"event {event.event_type} must be emitted from node {expected}, got {event.node}",
        )

    allowed = ALLOWED_FROM[event.event_type]
    if state.current_node not in allowed:
        return TransitionResult(
            False,
            reason=(
                f"illegal transition: {event.event_type} from current_node="
                f"{state.current_node!r} (allowed={sorted(str(x) for x in allowed)})"
            ),
        )

    # --- Actor isolation: builder and reviewer must differ ---
    if event.event_type in ("REVIEW_APPROVED", "REVIEW_REJECTED"):
        builder_id = state.builder_actor_id
        if builder_id and event.actor_id == builder_id:
            return TransitionResult(
                False,
                reason="builder cannot review own work (actor isolation)",
                blocker="builder_reviewer_same_actor",
            )
        if event.actor_role != "reviewer":
            return TransitionResult(False, reason="review events require actor_role=reviewer")

    if event.event_type == "BUILD_COMPLETED" and event.actor_role != "builder":
        return TransitionResult(False, reason="BUILD_COMPLETED requires actor_role=builder")

    if event.event_type == "BUILD_COMPLETED" and not event.head_sha:
        return TransitionResult(False, reason="BUILD_COMPLETED requires non-empty head_sha")

    if event.event_type == "INVESTIGATION_COMPLETED" and event.actor_role != "investigator":
        return TransitionResult(False, reason="INVESTIGATION_COMPLETED requires actor_role=investigator")

    # Reviewer must never merge — v0 forbids merge conclusions entirely
    if event.actor_role == "reviewer" and event.conclusion == "merge":
        return TransitionResult(
            False,
            reason="reviewer must not merge",
            blocker="reviewer_merge_forbidden",
        )

    # --- Human gate ---
    if event.event_type == "HUMAN_APPROVED":
        if event.actor_role != "human":
            return TransitionResult(False, reason="HUMAN_APPROVED requires actor_role=human")
        if not event.head_sha:
            return TransitionResult(False, reason="HUMAN_APPROVED requires head_sha")
        if not state.head_sha:
            return TransitionResult(False, reason="HUMAN_APPROVED requires current non-empty state.head_sha")
        if event.head_sha != state.head_sha:
            return TransitionResult(
                False,
                reason=(
                    f"HUMAN_APPROVED head_sha {event.head_sha} does not match "
                    f"current head_sha {state.head_sha}"
                ),
            )

    if event.event_type == "HUMAN_REJECTED" and event.actor_role != "human":
        return TransitionResult(False, reason="HUMAN_REJECTED requires actor_role=human")

    # Successful close path requires human approval of the current head
    if event.event_type == "HUMAN_APPROVED":
        # Will close successfully after reduce — gated here by role/sha checks above
        pass

    # --- Agent run budget ---
    if event.event_type in AGENT_RUN_EVENTS:
        if state.agent_run_count >= MAX_TOTAL_AGENT_RUNS:
            return TransitionResult(
                False,
                reason=f"agent run budget exhausted (max={MAX_TOTAL_AGENT_RUNS})",
                blocker="agent_run_budget_exhausted",
            )

    # --- Retry limits & duplicate failure signature ---
    if event.event_type == "NODE_FAILED":
        node = event.node
        retries = state.retry_count.get(node, 0)
        if retries >= MAX_RETRIES_PER_NODE:
            return TransitionResult(
                False,
                reason=f"retry exhaustion on node {node} (max={MAX_RETRIES_PER_NODE})",
                blocker=f"retry_exhausted:{node}",
            )

        sig = _failure_signature(event)
        if sig and sig in state.failure_signatures:
            return TransitionResult(
                False,
                reason=f"identical failure signature seen twice: {sig}",
                blocker=f"duplicate_failure:{sig}",
            )

        return TransitionResult(True, next_node=node)

    if event.event_type == "GRAPH_STOPPED":
        return TransitionResult(True, next_node="close")

    next_node = route(event.event_type)
    if next_node is None:
        return TransitionResult(False, reason=f"no route for {event.event_type}")

    return TransitionResult(True, next_node=next_node)


def _failure_signature(event: Event) -> Optional[str]:
    if not event.evidence:
        return event.conclusion
    return event.evidence.get("failure_signature") or event.conclusion
