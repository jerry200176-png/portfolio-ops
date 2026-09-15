"""Worker result contract shared by fake and production workers.

Workers propose an outcome; they must not choose next_node.
Canonical transitions are committed only by the durable graph runtime.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

RESULT_SCHEMA_VERSION = "1.0"

ALLOWED_OUTCOME_TYPES = frozenset(
    {
        "INVESTIGATION_COMPLETED",
        "BUILD_COMPLETED",
        "REVIEW_REJECTED",
        "REVIEW_APPROVED",
        "HUMAN_APPROVED",
        "HUMAN_REJECTED",
        "NODE_FAILED",
    }
)

# Default actor role expected for each proposed outcome type.
OUTCOME_ACTOR_ROLE = {
    "INVESTIGATION_COMPLETED": "investigator",
    "BUILD_COMPLETED": "builder",
    "REVIEW_REJECTED": "reviewer",
    "REVIEW_APPROVED": "reviewer",
    "HUMAN_APPROVED": "human",
    "HUMAN_REJECTED": "human",
    "NODE_FAILED": None,  # uses attempt node role
}

FORBIDDEN_WORKER_KEYS = frozenset({"next_node", "current_node", "run_status"})


class WorkerResultError(ValueError):
    """Structured worker result failed schema / policy validation."""


@dataclass(frozen=True)
class ProposedOutcome:
    outcome_type: str
    actor_id: str
    actor_role: str
    head_sha: Optional[str] = None
    base_sha: Optional[str] = None
    conclusion: Optional[str] = None
    evidence: Optional[dict[str, Any]] = None
    repository: Optional[str] = None


@dataclass(frozen=True)
class WorkerResult:
    status: str
    summary: str
    idempotency_key: str
    artifacts: tuple[dict[str, Any], ...]
    evidence: tuple[dict[str, Any], ...]
    proposed_outcome: Optional[ProposedOutcome]
    schema_version: str = RESULT_SCHEMA_VERSION
    raw: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "schema_version": self.schema_version,
            "status": self.status,
            "summary": self.summary,
            "idempotency_key": self.idempotency_key,
            "artifacts": list(self.artifacts),
            "evidence": list(self.evidence),
            "proposed_outcome": None,
        }
        if self.proposed_outcome is not None:
            po = self.proposed_outcome
            out["proposed_outcome"] = {
                "outcome_type": po.outcome_type,
                "actor_id": po.actor_id,
                "actor_role": po.actor_role,
                "head_sha": po.head_sha,
                "base_sha": po.base_sha,
                "conclusion": po.conclusion,
                "evidence": po.evidence,
                "repository": po.repository,
            }
        return out


def validate_worker_result(data: dict[str, Any]) -> WorkerResult:
    if not isinstance(data, dict):
        raise WorkerResultError("worker result must be a JSON object")

    for key in FORBIDDEN_WORKER_KEYS:
        if key in data:
            raise WorkerResultError(f"worker must not set {key}; graph runtime owns transitions")

    schema_version = data.get("schema_version", RESULT_SCHEMA_VERSION)
    if schema_version != RESULT_SCHEMA_VERSION:
        raise WorkerResultError(f"unsupported schema_version: {schema_version}")

    status = data.get("status")
    if status not in ("success", "failure", "needs_human"):
        raise WorkerResultError("status must be success|failure|needs_human")

    summary = data.get("summary")
    if not isinstance(summary, str) or not summary.strip():
        raise WorkerResultError("summary must be a non-empty string")

    idem = data.get("idempotency_key")
    if not isinstance(idem, str) or not idem.strip():
        raise WorkerResultError("idempotency_key is required")

    artifacts = data.get("artifacts", [])
    evidence = data.get("evidence", [])
    if not isinstance(artifacts, list) or not isinstance(evidence, list):
        raise WorkerResultError("artifacts and evidence must be lists")

    for item in artifacts:
        if not isinstance(item, dict) or "kind" not in item or "uri" not in item:
            raise WorkerResultError("each artifact requires kind and uri")

    for item in evidence:
        if not isinstance(item, dict) or "kind" not in item or "ref" not in item:
            raise WorkerResultError("each evidence item requires kind and ref")

    proposed_raw = data.get("proposed_outcome")
    proposed: Optional[ProposedOutcome] = None
    if proposed_raw is not None:
        if not isinstance(proposed_raw, dict):
            raise WorkerResultError("proposed_outcome must be an object")
        if "next_node" in proposed_raw:
            raise WorkerResultError("proposed_outcome must not include next_node")
        outcome_type = proposed_raw.get("outcome_type")
        if outcome_type not in ALLOWED_OUTCOME_TYPES:
            raise WorkerResultError(f"illegal proposed outcome_type: {outcome_type}")
        actor_id = proposed_raw.get("actor_id")
        actor_role = proposed_raw.get("actor_role")
        if not isinstance(actor_id, str) or not actor_id:
            raise WorkerResultError("proposed_outcome.actor_id is required")
        if not isinstance(actor_role, str) or not actor_role:
            raise WorkerResultError("proposed_outcome.actor_role is required")
        expected_role = OUTCOME_ACTOR_ROLE.get(outcome_type)
        if expected_role and actor_role != expected_role:
            raise WorkerResultError(
                f"proposed_outcome.actor_role must be {expected_role} for {outcome_type}"
            )
        proposed = ProposedOutcome(
            outcome_type=outcome_type,
            actor_id=actor_id,
            actor_role=actor_role,
            head_sha=proposed_raw.get("head_sha"),
            base_sha=proposed_raw.get("base_sha"),
            conclusion=proposed_raw.get("conclusion"),
            evidence=proposed_raw.get("evidence"),
            repository=proposed_raw.get("repository"),
        )

    if status == "success" and proposed is None:
        raise WorkerResultError("successful worker result requires proposed_outcome")

    return WorkerResult(
        schema_version=schema_version,
        status=status,
        summary=summary,
        idempotency_key=idem,
        artifacts=tuple(artifacts),
        evidence=tuple(evidence),
        proposed_outcome=proposed,
        raw=data,
    )


def write_worker_result(path: str | Path, result: WorkerResult | dict[str, Any]) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = result.to_dict() if isinstance(result, WorkerResult) else result
    validate_worker_result(payload)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def read_worker_result(path: str | Path) -> WorkerResult:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return validate_worker_result(data)
