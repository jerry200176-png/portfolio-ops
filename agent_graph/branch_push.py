"""Control-plane branch push (GitHub effects adjunct).

RealCodex builders commit locally; the control plane owns publishing the
branch so PR create can observe head without relying on Codex sandbox network.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any, Optional


class BranchPushError(RuntimeError):
    blocker = "branch_push_failed"


def ensure_branch_pushed(
    worktree: str | Path,
    *,
    remote: str = "origin",
    timeout_sec: float = 120.0,
) -> dict[str, Any]:
    """Push current HEAD to ``remote`` with upstream tracking.

    Idempotent when the remote already has the same tip.
    """
    wt = Path(worktree).resolve()
    if not wt.is_dir():
        raise BranchPushError(f"worktree missing: {wt}")

    def _git(*args: str) -> str:
        proc = subprocess.run(
            ["git", "-C", str(wt), *args],
            capture_output=True,
            text=True,
            timeout=timeout_sec,
            check=False,
        )
        if proc.returncode != 0:
            raise BranchPushError((proc.stderr or proc.stdout or "git failed").strip())
        return (proc.stdout or "").strip()

    branch = _git("branch", "--show-current")
    if not branch:
        raise BranchPushError("detached HEAD; refuse push without branch")
    head = _git("rev-parse", "HEAD")

    # Fast path: remote tip already matches.
    ls = subprocess.run(
        ["git", "-C", str(wt), "ls-remote", "--heads", remote, branch],
        capture_output=True,
        text=True,
        timeout=timeout_sec,
        check=False,
    )
    if ls.returncode == 0 and ls.stdout.strip():
        remote_sha = ls.stdout.split()[0].strip()
        if remote_sha == head:
            return {
                "pushed": False,
                "already_up_to_date": True,
                "branch": branch,
                "head_sha": head,
                "remote": remote,
            }

    _git("push", "-u", remote, "HEAD")
    return {
        "pushed": True,
        "already_up_to_date": False,
        "branch": branch,
        "head_sha": head,
        "remote": remote,
    }


def try_ensure_branch_pushed(
    worktree: Optional[str | Path],
    **kwargs: Any,
) -> Optional[dict[str, Any]]:
    if not worktree:
        return None
    return ensure_branch_pushed(worktree, **kwargs)
