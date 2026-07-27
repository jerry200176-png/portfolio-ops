"""Minimal data model for Agent Graph Runtime v0."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Optional

# Graph nodes (v0)
NODES = (
    "intake",
    "investigator",
    "builder",
    "reviewer",
    "human_gate",
    "close",
)

# Event types that drive routing
EVENT_TYPES = (
    "TASK_CREATED",
    "INVESTIGATION_COMPLETED",
    "BUILD_COMPLETED",
    "REVIEW_REJECTED",
    "REVIEW_APPROVED",
    "HUMAN_APPROVED",
    "HUMAN_REJECTED",
    "NODE_FAILED",
)

# Actor roles
ACTOR_ROLES = (
    "system",
    "investigator",
    "builder",
    "reviewer",
    "human",
)

# Budget limits
MAX_RETRIES_PER_NODE = 2
MAX_TOTAL_AGENT_RUNS = 6

# Agent-facing event types that consume the agent-run budget
AGENT_RUN_EVENTS = frozenset(
    {
        "INVESTIGATION_COMPLETED",
        "BUILD_COMPLETED",
        "REVIEW_REJECTED",
        "REVIEW_APPROVED",
        "NODE_FAILED",
    }
)

# Task status values produced by the reducer
TASK_STATUSES = (
    "pending",
    "investigating",
    "building",
    "reviewing",
    "human_approval_required",
    "closed_success",
    "closed_blocked",
    "blocked",
)


@dataclass(frozen=True)
class Event:
    """Append-only audit event. Fields are fixed for v0."""

    event_id: str
    task_id: str
    timestamp: str
    event_type: str
    node: str
    actor_id: str
    actor_role: str
    repository: str
    base_sha: Optional[str] = None
    head_sha: Optional[str] = None
    conclusion: Optional[str] = None
    evidence: Optional[dict[str, Any]] = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Event":
        return cls(
            event_id=data["event_id"],
            task_id=data["task_id"],
            timestamp=data["timestamp"],
            event_type=data["event_type"],
            node=data["node"],
            actor_id=data["actor_id"],
            actor_role=data["actor_role"],
            repository=data["repository"],
            base_sha=data.get("base_sha"),
            head_sha=data.get("head_sha"),
            conclusion=data.get("conclusion"),
            evidence=data.get("evidence"),
        )


@dataclass
class TaskState:
    """Reduced task state — fully rebuildable from the event log."""

    task_id: Optional[str] = None
    current_node: Optional[str] = None
    task_status: str = "pending"
    retry_count: dict[str, int] = field(default_factory=dict)
    agent_run_count: int = 0
    builder_actor_id: Optional[str] = None
    reviewer_actor_id: Optional[str] = None
    approved_head_sha: Optional[str] = None
    blocker: Optional[str] = None
    repository: Optional[str] = None
    base_sha: Optional[str] = None
    head_sha: Optional[str] = None
    failure_signatures: list[str] = field(default_factory=list)
    human_approved: bool = False
    closed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def snapshot(self) -> dict[str, Any]:
        """Stable dict for equality / replay checks."""
        return {
            "task_id": self.task_id,
            "current_node": self.current_node,
            "task_status": self.task_status,
            "retry_count": dict(sorted(self.retry_count.items())),
            "agent_run_count": self.agent_run_count,
            "builder_actor_id": self.builder_actor_id,
            "reviewer_actor_id": self.reviewer_actor_id,
            "approved_head_sha": self.approved_head_sha,
            "blocker": self.blocker,
            "repository": self.repository,
            "base_sha": self.base_sha,
            "head_sha": self.head_sha,
            "failure_signatures": list(self.failure_signatures),
            "human_approved": self.human_approved,
            "closed": self.closed,
        }
