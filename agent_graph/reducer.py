"""Deterministic reducer: TaskState is fully rebuildable from events."""

from __future__ import annotations

from typing import Any

from .models import AGENT_RUN_EVENTS, Event, TaskState
from .observation import parse_fact_from_evidence
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
        stopped=state.stopped,
        observations=dict(state.observations or {}),
    )

    if event.base_sha is not None:
        new.base_sha = event.base_sha

    # Head SHA change invalidates prior human approval and SHA-bound CI authority.
    if event.head_sha is not None and event.event_type != "EXTERNAL_OBSERVATION":
        if new.head_sha is not None and event.head_sha != new.head_sha:
            new.approved_head_sha = None
            new.human_approved = False
            new.observations = _invalidate_observations_for_head_move(
                new.observations, old_sha=new.head_sha, new_sha=event.head_sha
            )
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
        new.task_status = "waiting_for_approval"

    elif et == "HUMAN_APPROVED":
        new.human_approved = True
        new.approved_head_sha = event.head_sha or new.head_sha
        new.current_node = "approved_for_effect"
        new.task_status = "approved_for_effect"
        new.closed = False
        new.blocker = None

    elif et == "HUMAN_REJECTED":
        new.human_approved = False
        new.approved_head_sha = None
        new.current_node = "close"
        new.task_status = "closed_blocked"
        new.closed = True
        new.blocker = "human_rejected"

    elif et == "EFFECT_RECONCILED":
        new.current_node = "close"
        new.task_status = "closed_success"
        new.closed = True
        new.blocker = None

    elif et == "EXTERNAL_OBSERVATION":
        new.observations = _merge_observation(new.observations, event)
        # PR head move observed externally: invalidate approval if graph head differs.
        fact = parse_fact_from_evidence(event.evidence)
        if fact and fact.fact_type == "PR_HEAD_OBSERVED":
            observed = fact.observed_head_sha
            if new.head_sha and observed and observed != new.head_sha:
                new.approved_head_sha = None
                new.human_approved = False
                if new.task_status == "approved_for_effect":
                    new.task_status = "waiting_for_approval"
                    new.current_node = "human_gate"
            # Align Run head with observed PR head when observation is authoritative.
            if observed:
                if new.head_sha and observed != new.head_sha:
                    new.observations = _invalidate_observations_for_head_move(
                        new.observations, old_sha=new.head_sha, new_sha=observed
                    )
                new.head_sha = observed

    elif et == "NODE_FAILED":
        node = event.node
        new.retry_count[node] = new.retry_count.get(node, 0) + 1
        sig = _failure_signature(event)
        if sig:
            new.failure_signatures.append(sig)
        # Stay on same node for retry; status unchanged unless exhausted (validated upstream)
        new.current_node = node

    elif et == "GRAPH_STOPPED":
        new.current_node = event.node
        new.task_status = "blocked"
        new.blocker = (event.evidence or {}).get("blocker") or event.conclusion or "graph_stopped"
        new.stopped = True
        new.closed = False

    return new


def _merge_observation(observations: dict[str, Any], event: Event) -> dict[str, Any]:
    out = dict(observations or {})
    fact = parse_fact_from_evidence(event.evidence)
    if fact is None:
        return out
    facts = list(out.get("facts") or [])
    # Idempotent: replace same logical key rather than duplicate.
    key = fact.logical_key()
    facts = [f for f in facts if f.get("logical_key") != key]
    entry = fact.to_dict()
    entry["logical_key"] = key
    entry["event_id"] = event.event_id
    facts.append(entry)
    out["facts"] = facts

    ci_by_sha = dict(out.get("ci_by_sha") or {})
    if fact.fact_type in ("CI_PENDING", "CI_PASSED", "CI_FAILED"):
        ci_by_sha[fact.observed_head_sha] = fact.fact_type
    out["ci_by_sha"] = ci_by_sha

    pr_heads = dict(out.get("pr_head_by_ref") or {})
    if fact.fact_type in ("PR_HEAD_OBSERVED", "PR_EXISTS"):
        pr_heads[fact.external_ref] = fact.observed_head_sha
    out["pr_head_by_ref"] = pr_heads

    latest = dict(out.get("latest_by_type") or {})
    latest[fact.fact_type] = {
        "external_ref": fact.external_ref,
        "observed_head_sha": fact.observed_head_sha,
        "observed_at": fact.observed_at,
    }
    out["latest_by_type"] = latest
    return out


def _invalidate_observations_for_head_move(
    observations: dict[str, Any], *, old_sha: str, new_sha: str
) -> dict[str, Any]:
    """Keep history, but strip CI authority of the old SHA for authorization."""
    del new_sha
    out = dict(observations or {})
    ci_by_sha = dict(out.get("ci_by_sha") or {})
    if old_sha in ci_by_sha:
        # Mark superseded rather than deleting history facts list.
        ci_by_sha[old_sha] = f"SUPERSEDED:{ci_by_sha[old_sha]}"
    out["ci_by_sha"] = ci_by_sha
    out["head_move"] = {"from": old_sha, "invalidated_ci": True}
    return out


def can_close_successfully(state: TaskState) -> bool:
    """Security gate: successful close requires human approval of current head."""
    if not state.human_approved:
        return False
    if not state.approved_head_sha:
        return False
    if state.head_sha and state.approved_head_sha != state.head_sha:
        return False
    return state.task_status in ("closed_success", "approved_for_effect")


def approval_still_valid(state: TaskState) -> bool:
    """Founder approval is usable only for the exact approved head SHA."""
    if not state.human_approved or not state.approved_head_sha:
        return False
    if state.head_sha and state.approved_head_sha != state.head_sha:
        return False
    return True
