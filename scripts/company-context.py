#!/usr/bin/env python3
"""Print and validate the company context an agent must use before acting."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def load(name: str):
    return yaml.safe_load((ROOT / name).read_text(encoding="utf-8"))


def check() -> list[str]:
    errors: list[str] = []
    contract = load("governance/company-agent-contract.yaml")
    portfolio = load("portfolio.yaml")
    manifest = load("workspace.manifest.yaml")
    if contract.get("maintainer_model") != "single_owner":
        errors.append("contract maintainer_model must be single_owner")
    catalog_ids = {path.stem for path in (ROOT / "catalog").glob("*.yaml")}
    supported = set(contract.get("agent_entrypoints", {}).get("supported_projects", []))
    manifest_ids = {row.get("id") for row in manifest.get("repositories", [])}
    required = ("id", "name", "github_repo", "tier", "lifecycle", "data_sensitivity",
                "deploy_target", "last_verified_at", "source_commit", "evidence_expires_at")
    for project in portfolio.get("projects", []):
        project_id = project.get("id")
        for field in required:
            if project.get(field) is None or project.get(field) == "":
                errors.append(f"portfolio project {project_id}: missing {field}")
        if project_id not in catalog_ids:
            errors.append(f"portfolio project {project_id}: missing catalog/{project_id}.yaml")
        if project_id not in supported:
            errors.append(f"portfolio project {project_id}: missing from supported_projects")
    if any(row.get("id") == "portfolio-ops" for row in portfolio.get("meta", [])) and "portfolio-ops" not in manifest_ids:
        errors.append("workspace manifest is missing portfolio-ops")
    for name in ("CLAUDE.md", "AGENTS.md", "governance/company-agent-contract.yaml",
                 "docs/agent-operating-loop.md", "workspace.manifest.yaml"):
        if not (ROOT / name).is_file():
            errors.append(f"missing first-read file: {name}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    errors = check()
    if args.check:
        if errors:
            for error in errors:
                print(f"company-context: FAIL: {error}")
            return 1
        print("company-context: OK")
        return 0
    contract = load("governance/company-agent-contract.yaml")
    portfolio = load("portfolio.yaml")
    print(json.dumps({
        "company": contract.get("company_name"),
        "control_plane": contract.get("control_plane", {}).get("repository"),
        "default_mode": contract.get("agent_entrypoints", {}).get("default_mode"),
        "projects": [{"id": row.get("id"), "name": row.get("name"), "lifecycle": row.get("lifecycle")}
                     for row in portfolio.get("projects", [])],
        "operating_loop": [phase["id"] for phase in contract.get("delivery_loop", {}).get("phases", [])],
    }, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
