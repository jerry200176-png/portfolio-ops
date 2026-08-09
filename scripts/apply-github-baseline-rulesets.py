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
RULESET_FIELDS = ("name", "target", "enforcement", "conditions", "rules", "bypass_actors")


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


def ruleset_fingerprint(value: dict[str, Any]) -> str:
    """Compare only the declarative fields, ignoring GitHub-generated metadata."""
    return json.dumps(
        {field: value.get(field) for field in RULESET_FIELDS},
        sort_keys=True,
        separators=(",", ":"),
    )


def existing_action(existing: dict[str, Any], desired: dict[str, Any], replace_existing: bool) -> str:
    """Return a safe plan for an existing named ruleset."""
    if ruleset_fingerprint(existing) == ruleset_fingerprint(desired):
        return "unchanged"
    return "updated" if replace_existing else "blocked"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", action="append", help="Apply only this owner/repo")
    parser.add_argument("--apply", action="store_true", help="Write the ruleset to GitHub")
    parser.add_argument(
        "--replace-existing",
        action="store_true",
        help="Allow --apply to replace an existing ruleset whose declarative fields drift",
    )
    args = parser.parse_args()

    if args.replace_existing and not args.apply:
        parser.error("--replace-existing requires --apply")

    data = yaml.safe_load(MANIFEST.read_text())
    entries = data["repositories"]
    if args.repo:
        entries = [entry for entry in entries if entry["github_repo"] in args.repo]

    rule_payload = payload()
    plans: list[tuple[dict[str, Any], str, dict[str, Any] | None, dict[str, Any] | None]] = []
    for entry in entries:
        repo = entry["github_repo"]
        if not args.apply:
            print(f"DRY-RUN {repo}: create/update {RULESET_NAME}")
            continue

        existing = gh_json(repo, f"repos/{repo}/rulesets") or []
        match = next((item for item in existing if item.get("name") == RULESET_NAME), None)
        if not match:
            plans.append((entry, "created", None, None))
            continue

        detail = gh_json(repo, f"repos/{repo}/rulesets/{match['id']}") or match
        action = existing_action(detail, rule_payload, args.replace_existing)
        if action == "blocked":
            print(
                f"BLOCKED {repo}: existing {RULESET_NAME} differs; "
                "refusing to overwrite without --replace-existing",
                file=sys.stderr,
            )
            return 2
        plans.append((entry, action, match, detail))

    for entry, action, match, _detail in plans:
        repo = entry["github_repo"]
        if action == "unchanged":
            print(f"VERIFIED {repo}: unchanged {RULESET_NAME}")
            continue
        if action == "created":
            result = gh_json(repo, "--method", "POST", f"repos/{repo}/rulesets", body=rule_payload)
        else:
            assert match is not None
            result = gh_json(repo, "--method", "PUT", f"repos/{repo}/rulesets/{match['id']}", body=rule_payload)
        if result is None:
            return 1
        print(f"APPLIED {repo}: {action} {RULESET_NAME}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
