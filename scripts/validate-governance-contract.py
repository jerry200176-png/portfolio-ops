#!/usr/bin/env python3
"""Validate the machine-readable portfolio and workspace contracts.

The default mode validates structure only so it is safe to run in CI.  Use
--check-paths from the real workspace to additionally verify local paths.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

import yaml


ROOT = Path(__file__).resolve().parents[1]


def load_yaml(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        value = yaml.safe_load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected a mapping")
    return value


def require(mapping: dict, keys: tuple[str, ...], label: str, errors: list[str]) -> None:
    for key in keys:
        if key not in mapping or mapping[key] in (None, ""):
            errors.append(f"{label}: missing {key}")


def validate_manifest(errors: list[str], check_paths: bool) -> None:
    path = ROOT / "workspace.manifest.yaml"
    manifest = load_yaml(path)
    require(
        manifest,
        ("schema_version", "workspace_root", "manifest_owner", "last_verified_at", "inventory_policy", "paths", "repositories"),
        "workspace.manifest.yaml",
        errors,
    )

    paths = manifest.get("paths", {})
    if isinstance(paths, dict):
        require(
            paths,
            ("bare_repos", "canonical_checkouts", "active_worktrees", "tasks", "archives", "evidence", "backups", "agent_control", "control_plane"),
            "workspace.manifest.yaml.paths",
            errors,
        )

    policy = manifest.get("inventory_policy", {})
    if isinstance(policy, dict):
        require(
            policy,
            ("discover_immediate_git_roots", "worktree_roots", "forbidden_mutations"),
            "workspace.manifest.yaml.inventory_policy",
            errors,
        )

    repositories = manifest.get("repositories", [])
    if not isinstance(repositories, list) or not repositories:
        errors.append("workspace.manifest.yaml.repositories: expected a non-empty list")
        return

    ids: set[str] = set()
    paths_seen: set[str] = set()
    allowed_roles = {"canonical-checkout", "control-plane", "active-worktree", "legacy-checkout", "legacy-worktree"}
    for index, repository in enumerate(repositories):
        label = f"workspace.manifest.yaml.repositories[{index}]"
        if not isinstance(repository, dict):
            errors.append(f"{label}: expected a mapping")
            continue
        require(repository, ("id", "path", "role", "remote", "branch_policy", "mutation_policy", "approval_for_archive_or_remove"), label, errors)
        repo_id = repository.get("id")
        repo_path = repository.get("path")
        if repo_id in ids:
            errors.append(f"{label}: duplicate id {repo_id}")
        if repo_path in paths_seen:
            errors.append(f"{label}: duplicate path {repo_path}")
        if repo_id:
            ids.add(repo_id)
        if repo_path:
            paths_seen.add(repo_path)
        if repository.get("role") not in allowed_roles:
            errors.append(f"{label}: unsupported role {repository.get('role')}")
        if check_paths and isinstance(repo_path, str) and not Path(repo_path).exists():
            errors.append(f"{label}: path does not exist: {repo_path}")


def validate_portfolio(errors: list[str], check_paths: bool) -> None:
    path = ROOT / "portfolio.yaml"
    portfolio = load_yaml(path)
    require(portfolio, ("schema_version", "updated_at", "projects"), "portfolio.yaml", errors)
    freshness = portfolio.get("freshness", {})
    require(freshness, ("p0_evidence_ttl_hours", "inventory_ttl_days", "status_ttl_hours"), "portfolio.yaml.freshness", errors)
    baseline = portfolio.get("governance_baseline", {})
    require(baseline, ("manifest", "component_contract", "last_inventory_at", "inventory_rows", "unresolved_inventory_rows"), "portfolio.yaml.governance_baseline", errors)

    projects = portfolio.get("projects", [])
    if not isinstance(projects, list) or not projects:
        errors.append("portfolio.yaml.projects: expected a non-empty list")
        return
    ids: set[str] = set()
    for index, project in enumerate(projects):
        label = f"portfolio.yaml.projects[{index}]"
        if not isinstance(project, dict):
            errors.append(f"{label}: expected a mapping")
            continue
        require(
            project,
            ("id", "name", "local_path", "github_repo", "tier", "lifecycle", "production_status", "latest_activity", "open_p0", "open_p1", "current_priority", "next_action", "evidence_links"),
            label,
            errors,
        )
        if project.get("id") in ids:
            errors.append(f"{label}: duplicate id {project.get('id')}")
        if project.get("id"):
            ids.add(project["id"])
        if check_paths and isinstance(project.get("local_path"), str) and not Path(project["local_path"]).exists():
            errors.append(f"{label}: local_path does not exist: {project['local_path']}")


def validate_catalog(errors: list[str]) -> None:
    catalog_dir = ROOT / "catalog"
    files = sorted(catalog_dir.glob("*.yaml")) if catalog_dir.is_dir() else []
    if not files:
        errors.append("catalog: no component contract files found")
        return
    seen: set[str] = set()
    required = ("apiVersion", "kind", "metadata", "spec")
    for path in files:
        label = str(path.relative_to(ROOT))
        try:
            component = load_yaml(path)
        except (OSError, ValueError, yaml.YAMLError) as exc:
            errors.append(f"{label}: {exc}")
            continue
        require(component, required, label, errors)
        metadata = component.get("metadata", {})
        spec = component.get("spec", {})
        if not isinstance(metadata, dict) or not isinstance(spec, dict):
            errors.append(f"{label}: metadata and spec must be mappings")
            continue
        require(metadata, ("name", "description", "annotations"), f"{label}.metadata", errors)
        require(spec, ("owner", "lifecycle", "tier", "dataSensitivity", "deployTarget", "healthUrl", "versionUrl", "recoveryOwner", "lastVerifiedAt", "evidenceTtlHours"), f"{label}.spec", errors)
        name = metadata.get("name")
        if name in seen:
            errors.append(f"{label}: duplicate component name {name}")
        if name:
            seen.add(name)


def validate_enforcement_policy(errors: list[str]) -> None:
    path = ROOT / "governance/github-enforcement-policy.yaml"
    policy = load_yaml(path)
    require(
        policy,
        ("schema_version", "policy_owner", "maintainer_model", "default_branch", "required_approvals", "require_code_owner_review", "required_review_thread_resolution", "block_force_push", "block_branch_deletion", "allow_bypass_actors", "emergency_bypass", "repositories"),
        "governance/github-enforcement-policy.yaml",
        errors,
    )
    if policy.get("maintainer_model") == "single_owner":
        if policy.get("required_approvals") != 0 or policy.get("require_code_owner_review") is not False:
            errors.append("governance/github-enforcement-policy.yaml: single_owner mode must disable approval and CODEOWNER requirements")
    elif policy.get("required_approvals", 0) < 1:
        errors.append("governance/github-enforcement-policy.yaml: required_approvals must be at least 1 unless maintainer_model is single_owner")
    repositories = policy.get("repositories", [])
    if not isinstance(repositories, list) or not repositories:
        errors.append("governance/github-enforcement-policy.yaml.repositories: expected a non-empty list")
        return
    seen: set[str] = set()
    for index, repository in enumerate(repositories):
        label = f"governance/github-enforcement-policy.yaml.repositories[{index}]"
        if not isinstance(repository, dict):
            errors.append(f"{label}: expected a mapping")
            continue
        require(repository, ("id", "github_repo", "critical_paths", "required_status_checks"), label, errors)
        if repository.get("id") in seen:
            errors.append(f"{label}: duplicate id {repository.get('id')}")
        if repository.get("id"):
            seen.add(repository["id"])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-paths", action="store_true", help="also verify local filesystem paths")
    args = parser.parse_args()
    errors: list[str] = []
    try:
        validate_manifest(errors, args.check_paths)
        validate_portfolio(errors, args.check_paths)
        validate_catalog(errors)
        validate_enforcement_policy(errors)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        errors.append(str(exc))

    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print("PASS: governance contracts valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
