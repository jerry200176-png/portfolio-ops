"""Read-only GitHub / CI observation facts (Phase 1C).

Adapters produce ObservableFact only. They never mutate GitHub state and
never choose graph transitions — Observation → verifier → Event → reducer.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal, Optional

FACT_TYPES = (
    "PR_EXISTS",
    "PR_HEAD_OBSERVED",
    "CI_PENDING",
    "CI_PASSED",
    "CI_FAILED",
    "PR_MERGEABLE",
    "PR_MERGED_EXTERNALLY",
)

FactType = Literal[
    "PR_EXISTS",
    "PR_HEAD_OBSERVED",
    "CI_PENDING",
    "CI_PASSED",
    "CI_FAILED",
    "PR_MERGEABLE",
    "PR_MERGED_EXTERNALLY",
]


def _utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass(frozen=True)
class ObservableFact:
    """Single external observation bound to an exact head SHA."""

    fact_type: str
    source: str
    external_ref: str
    observed_at: str
    observed_head_sha: str
    evidence_ref: Optional[str] = None
    raw: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def logical_key(self) -> str:
        """Idempotency key for the same logical observation."""
        material = "|".join(
            [
                self.fact_type,
                self.source,
                self.external_ref,
                self.observed_head_sha,
                (self.raw or {}).get("conclusion") or "",
            ]
        )
        digest = hashlib.sha256(material.encode("utf-8")).hexdigest()[:24]
        return f"obs:{digest}"


def fact_event_id(run_id: str, fact: ObservableFact) -> str:
    return f"{run_id}:{fact.logical_key()}"


def serialize_fact_evidence(fact: ObservableFact) -> dict[str, Any]:
    return {
        "fact_type": fact.fact_type,
        "source": fact.source,
        "external_ref": fact.external_ref,
        "observed_at": fact.observed_at,
        "observed_head_sha": fact.observed_head_sha,
        "evidence_ref": fact.evidence_ref,
        "raw": fact.raw,
    }


def parse_fact_from_evidence(evidence: Optional[dict[str, Any]]) -> Optional[ObservableFact]:
    if not evidence or not evidence.get("fact_type"):
        return None
    return ObservableFact(
        fact_type=str(evidence["fact_type"]),
        source=str(evidence.get("source") or "unknown"),
        external_ref=str(evidence.get("external_ref") or ""),
        observed_at=str(evidence.get("observed_at") or ""),
        observed_head_sha=str(evidence.get("observed_head_sha") or ""),
        evidence_ref=evidence.get("evidence_ref"),
        raw=dict(evidence.get("raw") or {}),
    )


def ci_authorizes_head(observations: dict[str, Any], head_sha: str) -> bool:
    """CI green for SHA A does not authorize SHA B."""
    if not head_sha:
        return False
    by_sha = (observations or {}).get("ci_by_sha") or {}
    return by_sha.get(head_sha) == "CI_PASSED"


def dump_json(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"))
