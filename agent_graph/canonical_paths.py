"""Canonical control-plane path boundary helpers.

Worker workspace-write scope is the bound task worktree only.
Canonical SQLite (and WAL/SHM) must live outside that worktree.
"""

from __future__ import annotations

import os
from pathlib import Path


# Fleet-local control-plane state — outside /home/jerry/workspace/tasks/* worktrees.
DEFAULT_CANONICAL_DB = Path("/home/jerry/workspace/state/portfolio-ops/graph-control.sqlite")


class CanonicalPathError(ValueError):
    """Canonical store path violates worker writable boundary."""


def default_canonical_db_path() -> Path:
    override = os.environ.get("GRAPH_CONTROL_DB")
    if override:
        return Path(override).expanduser().resolve()
    return DEFAULT_CANONICAL_DB


def ensure_canonical_db_parent(path: Path) -> Path:
    path = Path(path).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def is_relative_to(path: Path, root: Path) -> bool:
    try:
        Path(path).resolve().relative_to(Path(root).resolve())
        return True
    except ValueError:
        return False


def assert_canonical_db_outside_worktree(db_path: Path | str, worktree: Path | str) -> None:
    """Fail closed if the canonical DB is inside the worker writable worktree."""
    db = Path(db_path).expanduser().resolve()
    wt = Path(worktree).expanduser().resolve()
    if not wt.is_dir():
        raise CanonicalPathError(f"worktree is not a directory: {wt}")
    # DB file, WAL, and SHM siblings must all stay outside the worktree.
    candidates = [db, Path(str(db) + "-wal"), Path(str(db) + "-shm"), db.parent]
    for cand in candidates:
        if is_relative_to(cand, wt):
            raise CanonicalPathError(
                f"canonical store path {cand} is inside worker worktree {wt}; "
                "refuse RealCodex launch (workspace-write would allow mutation)"
            )


def worktree_resource_key(worktree: Path | str) -> str:
    return f"worktree:{Path(worktree).expanduser().resolve()}"


def run_node_resource_key(run_id: str, node: str) -> str:
    return f"run:{run_id}:node:{node}"


def safe_result_path(worktree: Path | str) -> Path:
    """Controller-fixed result path; reject symlink/path escape from .agent-session."""
    from .worker_contract import RESULT_REL_PATH

    wt = Path(worktree).expanduser().resolve()
    session = (wt / ".agent-session").resolve()
    # Build expected path without following a malicious pre-existing symlink on
    # intermediate components where possible: resolve worktree, then join.
    expected = (wt / RESULT_REL_PATH)
    # If result.json is a symlink, resolve and require it stay under session.
    if expected.is_symlink() or expected.exists():
        resolved = expected.resolve()
    else:
        # Parent .agent-session must not be a symlink escaping the worktree.
        if (wt / ".agent-session").is_symlink():
            session_resolved = (wt / ".agent-session").resolve()
            if not is_relative_to(session_resolved, wt):
                raise CanonicalPathError(
                    f".agent-session symlink escapes worktree: {session_resolved}"
                )
            session = session_resolved
        resolved = (session / Path(RESULT_REL_PATH).name).resolve()

    if not is_relative_to(resolved, session) and resolved.parent != session:
        # Also allow exact session/result.json
        if resolved.parent.resolve() != session:
            raise CanonicalPathError(
                f"result path escapes .agent-session: {resolved} (session={session})"
            )
    if not is_relative_to(resolved, wt):
        raise CanonicalPathError(f"result path escapes worktree: {resolved}")
    return resolved
