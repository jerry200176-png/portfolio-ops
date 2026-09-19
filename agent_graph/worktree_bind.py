"""Optional binding helpers around existing agent-control gateway.

Does not rewrite agent-start. Real product-write launches should still use
agent-start so cwd is the task worktree.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, Optional


DEFAULT_AGENT_START = "/home/jerry/workspace/agent-control/bin/agent-start"

# Commits must attribute to the GitHub account or ruleset
# require_extra_approval_for_unattributed_changes blocks merge.
DEFAULT_GIT_AUTHOR_NAME = "jerry200176-png"
DEFAULT_GIT_AUTHOR_EMAIL = "jerry200176-png@users.noreply.github.com"


def ensure_github_attribution(
    worktree: str | Path,
    *,
    name: str = DEFAULT_GIT_AUTHOR_NAME,
    email: str = DEFAULT_GIT_AUTHOR_EMAIL,
) -> dict[str, str]:
    """Set local worktree git identity for GitHub-attributed commits."""
    wt = Path(worktree).resolve()
    if not wt.is_dir():
        raise FileNotFoundError(f"worktree not found: {wt}")
    subprocess.run(
        ["git", "-C", str(wt), "config", "user.name", name],
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["git", "-C", str(wt), "config", "user.email", email],
        check=True,
        capture_output=True,
        text=True,
    )
    return {"user.name": name, "user.email": email}


def bind_existing_worktree(
    runtime,
    run_id: str,
    *,
    worktree: str,
    branch: Optional[str] = None,
    base_sha: Optional[str] = None,
) -> dict[str, Any]:
    worktree_path = Path(worktree).resolve()
    if not worktree_path.is_dir():
        raise FileNotFoundError(f"worktree not found: {worktree_path}")
    if branch is None:
        branch = subprocess.run(
            ["git", "-C", str(worktree_path), "branch", "--show-current"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    if base_sha is None:
        base_sha = subprocess.run(
            ["git", "-C", str(worktree_path), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    run = runtime.bind_worktree(
        run_id, worktree=str(worktree_path), branch=branch, base_sha=base_sha
    )
    return run.to_dict()


def create_worktree_via_agent_start(
    *,
    project: str,
    task_id: str,
    agent_start: str = DEFAULT_AGENT_START,
    dry_run: bool = True,
) -> str:
    """Create an isolated worktree using the existing gateway (no CLI launch)."""
    cmd = [agent_start, project, task_id]
    if dry_run:
        cmd.append("--dry-run")
    proc = subprocess.run(cmd, check=True, capture_output=True, text=True)
    # Last non-empty line is the worktree path.
    lines = [ln.strip() for ln in proc.stdout.splitlines() if ln.strip()]
    if not lines:
        raise RuntimeError("agent-start produced no worktree path")
    return lines[-1]


def read_graph_binding(worktree: str | Path) -> Optional[dict[str, Any]]:
    path = Path(worktree) / ".agent-session" / "graph-binding.json"
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))
