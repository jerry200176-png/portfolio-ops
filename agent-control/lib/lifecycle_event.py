"""Canonical task lifecycle event contract shared by agent adapters."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

LIFECYCLE_STATES = frozenset({"terminal_success", "terminal_failed", "aborted", "idle"})
REQUIRED_FIELDS = ("task_id", "worktree", "completion_state", "source", "timestamp", "session_id")
TASK_ID_RE = re.compile(r"^[0-9A-Za-z][0-9A-Za-z._-]{0,63}$")


def make_event(task_id: str, worktree: str | Path, completion_state: str,
               source: str, timestamp: str | None = None) -> dict[str, str]:
    """Build and validate the five-field portable completion event."""
    event = {
        "task_id": task_id,
        "worktree": str(Path(worktree).resolve()),
        "completion_state": completion_state,
        "source": source,
        "timestamp": timestamp or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "session_id": _session_id(Path(worktree).resolve()),
    }
    return validate_event(event)


def validate_event(value: object) -> dict[str, str]:
    if not isinstance(value, dict) or any(key not in value for key in REQUIRED_FIELDS):
        raise ValueError("lifecycle event must contain task_id, worktree, completion_state, source, timestamp")
    event = {key: value[key] for key in REQUIRED_FIELDS}
    if not isinstance(event["task_id"], str) or not TASK_ID_RE.fullmatch(event["task_id"]):
        raise ValueError("invalid task_id")
    if not isinstance(event["worktree"], str) or not Path(event["worktree"]).is_absolute():
        raise ValueError("worktree must be an absolute path")
    if not isinstance(event["completion_state"], str) or event["completion_state"] not in LIFECYCLE_STATES:
        raise ValueError("invalid completion_state")
    if not isinstance(event["source"], str) or not event["source"].strip():
        raise ValueError("source must be a non-empty string")
    if not isinstance(event["session_id"], str) or not event["session_id"].strip():
        raise ValueError("session_id must identify the current agent-control session")
    if not isinstance(event["timestamp"], str):
        raise ValueError("timestamp must be an ISO-8601 string")
    try:
        parsed = datetime.fromisoformat(event["timestamp"].replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("timestamp must be an ISO-8601 string") from exc
    if parsed.tzinfo is None:
        raise ValueError("timestamp must include a timezone")
    return event


def _session_id(worktree: Path) -> str:
    """Bind completion to this worktree's current agent-control session."""
    manifest = worktree / ".agent-session" / "manifest.json"
    if manifest.is_symlink() or not manifest.is_file():
        raise ValueError("current worktree session manifest is missing or unsafe")
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ValueError("current worktree session manifest is unreadable") from exc
    session_id = data.get("session_id") if isinstance(data, dict) else None
    if not isinstance(session_id, str) or not session_id.strip():
        raise ValueError("current worktree session id is missing")
    return session_id


def event_id(event: dict[str, str]) -> str:
    canonical = json.dumps(validate_event(event), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
