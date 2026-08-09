"""Append-only in-memory event store (dry-run; no external I/O)."""

from __future__ import annotations

from typing import Iterable, Optional

from .models import Event


class AppendOnlyEventStore:
    """Events may only be appended. Existing events are never mutated or removed."""

    def __init__(self) -> None:
        self._events: list[Event] = []
        self._ids: set[str] = set()

    def __len__(self) -> int:
        return len(self._events)

    def append(self, event: Event) -> bool:
        """Append event. Returns False if event_id already exists (idempotent no-op).

        Raises ValueError if a caller attempts to replace or mutate an existing event.
        """
        if event.event_id in self._ids:
            return False
        self._events.append(event)
        self._ids.add(event.event_id)
        return True

    def overwrite(self, _event: Event) -> None:
        """Explicitly forbidden — events are append-only."""
        raise ValueError("event store is append-only; overwrite is forbidden")

    def replace_all(self, _events: Iterable[Event]) -> None:
        raise ValueError("event store is append-only; replace_all is forbidden")

    def all(self) -> list[Event]:
        return list(self._events)

    def for_task(self, task_id: str) -> list[Event]:
        return [e for e in self._events if e.task_id == task_id]

    def get(self, event_id: str) -> Optional[Event]:
        for e in self._events:
            if e.event_id == event_id:
                return e
        return None

    def has(self, event_id: str) -> bool:
        return event_id in self._ids
