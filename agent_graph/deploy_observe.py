"""Read-only deployment / runtime observation helpers.

Does NOT dispatch workflows or mutate production. Graph must not gain
production deploy authority through this module.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from typing import Any, Optional


class DeployObserveError(RuntimeError):
    pass


@dataclass
class RuntimeIdentity:
    health_ok: bool
    serving_sha: Optional[str]
    raw: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "health_ok": self.health_ok,
            "serving_sha": self.serving_sha,
            "raw": self.raw,
        }


def observe_workflow_runs(*, repo: str, limit: int = 5) -> list[dict[str, Any]]:
    """List recent workflow runs (read-only). Never `gh workflow run`."""
    proc = subprocess.run(
        [
            "gh",
            "run",
            "list",
            "--repo",
            repo,
            "--limit",
            str(limit),
            "--json",
            "databaseId,name,status,conclusion,headSha,url,createdAt",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise DeployObserveError((proc.stderr or proc.stdout).strip())
    return json.loads(proc.stdout or "[]")


def note_portfolio_ops_has_no_product_deploy() -> dict[str, Any]:
    return {
        "repo": "jerry200176-png/portfolio-ops",
        "product_deploy_path": None,
        "graph_production_deploy_authority": False,
        "reason": "portfolio-ops is the control plane; product deploys stay on product repos",
    }
