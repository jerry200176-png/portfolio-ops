#!/usr/bin/env python3
"""Create the non-bypass baseline ruleset for every governed GitHub repo.

The default is a dry run. ``--apply`` is deliberately required because this
changes GitHub repository enforcement. The ExoProtocol status check is added
in a later rollout stage, after each repository has a passing workflow.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "governance" / "repository-governance.yaml"
RULESET_NAME = "portfolio-governance-main"


def payload() -> dict[str, Any]:
    return {
        "name": RULESET_NAME,
        "target": "branch",
        "enforcement": "active",
        "conditions": {"ref_name": {"include": ["~DEFAULT_BRANCH"], "exclude": []}},
        "rules": [
            {"type": "deletion"},
            {"type": "non_fast_forward"},
            {
                "type": "pull_request",
                "parameters": {
                    "required_approving_review_count": 1,
                    "dismiss_stale_reviews_on_push": True,
                    "require_code_owner_review": False,
                    "require_last_push_approval": True,
                    "required_review_thread_resolution": True,
                    "required_reviewers": [],
                    "allowed_merge_methods": ["merge", "squash", "rebase"],
                },
            },
        ],
        "bypass_actors": [],
    }


def gh_json(repo: str, *args: str, body: dict[str, Any] | None = None) -> Any | None:
    command = ["gh", "api", *args]
    if body is not None:
        command.extend(["--input", "-"])
    result = subprocess.run(
        command,
        input=json.dumps(body) if body is not None else None,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        print(f"FAIL {repo}: {result.stderr.strip()}", file=sys.stderr)
        return None
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", action="append", help="Apply only this owner/repo")
    parser.add_argument("--apply", action="store_true", help="Write the ruleset to GitHub")
    args = parser.parse_args()

    data = yaml.safe_load(MANIFEST.read_text())
    entries = data["repositories"]
    if args.repo:
        entries = [entry for entry in entries if entry["github_repo"] in args.repo]

    rule_payload = payload()
    for entry in entries:
        repo = entry["github_repo"]
        if not args.apply:
            print(f"DRY-RUN {repo}: create/update {RULESET_NAME}")
            continue

        existing = gh_json(repo, f"repos/{repo}/rulesets") or []
        match = next((item for item in existing if item.get("name") == RULESET_NAME), None)
        if match:
            result = gh_json(repo, "--method", "PUT", f"repos/{repo}/rulesets/{match['id']}", body=rule_payload)
            action = "updated"
        else:
            result = gh_json(repo, "--method", "POST", f"repos/{repo}/rulesets", body=rule_payload)
            action = "created"
        if result is None:
            return 1
        print(f"APPLIED {repo}: {action} {RULESET_NAME}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
