"""Durable control-plane domain models (Phase 1A).

These sit beside the in-memory v0 Event/TaskState graph models.
Canonical persistence is SQLite; Codex processes never own this state.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Optional

GRAPH_VERSION = "v0"

RUN_STATUSES = (
    "pending",
    "running",
    "waiting_worker",
    "human_approval_required",
    "closed_success",
    "closed_blocked",
    "blocked",
)

ATTEMPT_STATUSES = (
    "started",
    "succeeded",
    "failed",
    "rejected",
    "ingested",
)


@dataclass(frozen=True)
class Goal:
    goal_id: str
    objective: str
    project: str
    risk_tier: str = "low"
    success_condition: Optional[str] = None
    created_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Run:
    """Materialized current-state projection of a Run (reducer output)."""

    run_id: str
    goal_id: str
    project: str
    graph_version: str
    risk_tier: str
    status: str
    current_node: Optional[str]
    worktree: Optional[str] = None
    branch: Optional[str] = None
    base_sha: Optional[str] = None
    head_sha: Optional[str] = None
    tested_sha: Optional[str] = None
    created_at: str = ""
    updated_at: str = ""
    blocker: Optional[str] = None
    closed: bool = False
    stopped: bool = False
    human_approved: bool = False
    graph_snapshot: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CanonicalEvent:
    """Append-only canonical history record."""

    event_id: str
    run_id: str
    type: str
    payload: dict[str, Any]
    created_at: str
    attempt_id: Optional[str] = None
    evidence_refs: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "run_id": self.run_id,
            "attempt_id": self.attempt_id,
            "type": self.type,
            "payload": dict(self.payload),
            "evidence_refs": list(self.evidence_refs),
            "created_at": self.created_at,
        }


@dataclass
class Attempt:
    attempt_id: str
    run_id: str
    node: str
    worker_type: str
    status: str
    started_at: str
    ended_at: Optional[str] = None
    model_profile: Optional[str] = None
    worker_pid: Optional[int] = None
    result_ingest_key: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Artifact:
    artifact_id: str
    run_id: str
    kind: str
    uri: str
    created_at: str
    attempt_id: Optional[str] = None
    sha256: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Evidence:
    """Reference to observable proof; content lives outside the Run row."""

    evidence_id: str
    kind: str
    ref: str
    summary: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Worker:
    """Replaceable worker identity (not durable Run owner)."""

    worker_type: str
    model_profile: Optional[str] = None
    pid: Optional[int] = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# Minimal schema interfaces for later phases (no full behavior in 1A).
@dataclass(frozen=True)
class Lease:
    lease_id: str
    resource_key: str
    created_at: str
    run_id: Optional[str] = None
    owner: Optional[str] = None
    fencing_token: int = 0
    expires_at: Optional[str] = None


@dataclass(frozen=True)
class Approval:
    approval_id: str
    run_id: str
    scope: str
    created_at: str
    status: str = "pending"
    actor: Optional[str] = None
    bound_head_sha: Optional[str] = None
    decided_at: Optional[str] = None
