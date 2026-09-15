"""Allowlisted external effects for the Graph Effect Journal.

Production deploy / workflow_dispatch / product host mutation are NOT allowlisted.
Portfolio-ops PR create/comment/merge are the only mutating GitHub verbs.
"""

from __future__ import annotations

ALLOWED_ACTIONS = frozenset({
    "github_pr_create",
    "github_pr_comment",
    "github_pr_merge",
})

# Repos that may receive Graph-driven PR mutations (control plane only).
ALLOWED_REPOS = frozenset({
    "jerry200176-png/portfolio-ops",
})

FORBIDDEN_ACTIONS = frozenset({
    "deploy",
    "production_deploy",
    "workflow_dispatch",
    "production_db_write",
    "migration",
    "ssh_production",
})


def assert_effect_allowed(*, action: str, repo: str) -> None:
    action_n = (action or "").strip()
    repo_n = (repo or "").strip()
    if action_n in FORBIDDEN_ACTIONS or action_n.startswith("deploy"):
        raise PermissionError(
            f"effect action {action_n!r} is forbidden (production mutation disabled)"
        )
    if action_n not in ALLOWED_ACTIONS:
        raise PermissionError(f"effect action {action_n!r} not in allowlist")
    if repo_n not in ALLOWED_REPOS:
        raise PermissionError(f"effect repo {repo_n!r} not in allowlist")
