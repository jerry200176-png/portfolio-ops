"""Minimal Effect Journal stub (Phase 1C).

External mutations are forbidden in this phase. The interface exists so
Observation / Approval can reference a future effect executor without
running merge, deploy, or production writes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional, Protocol


@dataclass(frozen=True)
class EffectIntent:
    """Declared but not executed effect (Phase 1C records intent only)."""

    effect_id: str
    run_id: str
    action: str
    head_sha: str
    created_at: str
    status: str = "declared"  # declared|blocked|executed (executed forbidden in 1C)
    external_ref: Optional[str] = None
    evidence: Optional[dict[str, Any]] = None


class EffectJournal(Protocol):
    def declare(self, intent: EffectIntent) -> EffectIntent: ...


class NoopEffectJournal:
    """Records intents in memory; never mutates external systems."""

    def __init__(self) -> None:
        self.intents: list[EffectIntent] = []

    def declare(self, intent: EffectIntent) -> EffectIntent:
        if intent.status == "executed":
            raise RuntimeError("Phase 1C forbids executing external effects")
        self.intents.append(intent)
        return intent
