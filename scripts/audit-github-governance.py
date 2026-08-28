#!/usr/bin/env python3
"""Read-only fleet audit for repository governance coverage.

This intentionally audits GitHub's enforcement boundary and repository
adapters; generic lint/security policy remains delegated to the OSS tools that
own those checks.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover - depends on the host runtime
    raise SystemExit("PyYAML is required: python3 -m pip install pyyaml") from exc


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "governance" / "repository-governance.yaml"


def gh_json(*args: str) -> Any | None:
    result = subprocess.run(
        ["gh", "api", *args],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return None


def ruleset_targets_main(ruleset: dict[str, Any]) -> bool:
    if ruleset.get("target") != "branch" or ruleset.get("enforcement") != "active":
        return False
    includes = ruleset.get("conditions", {}).get("ref_name", {}).get("include", [])
    return "~DEFAULT_BRANCH" in includes or "refs/heads/main" in includes


def ruleset_requires_review(ruleset: dict[str, Any]) -> bool:
    for rule in ruleset.get("rules", []):
        if rule.get("type") == "pull_request":
            return rule.get("parameters", {}).get("required_approving_review_count", 0) >= 1
    return False


def audit(entry: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    repo = entry["github_repo"]
    root_listing = gh_json(f"repos/{repo}/contents") or []
    root_names = {item.get("name") for item in root_listing if isinstance(item, dict)}
    missing_adapters = [name for name in entry["required_adapters"] if name not in root_names]

    ruleset_index = gh_json(f"repos/{repo}/rulesets") or []
    rulesets = []
    for ruleset in ruleset_index:
        ruleset_id = ruleset.get("id")
        detail = gh_json(f"repos/{repo}/rulesets/{ruleset_id}") if ruleset_id else None
        rulesets.append(detail or ruleset)
    main_rulesets = [rule for rule in rulesets if ruleset_targets_main(rule)]
    protected = bool(main_rulesets)
    review_required = any(ruleset_requires_review(rule) for rule in main_rulesets)

    branch_protection = gh_json(f"repos/{repo}/branches/main/protection")
    if isinstance(branch_protection, dict):
        protected = True
        review_required = review_required or bool(
            branch_protection.get("required_pull_request_reviews")
        )

    workflow_present = ".github" in root_names and gh_json(
        f"repos/{repo}/contents/.github/workflows/exo-governance.yml"
    ) is not None

    return {
        "id": entry["id"],
        "github_repo": repo,
        "lifecycle": entry["lifecycle"],
        "missing_adapters": missing_adapters,
        "main_protected": protected,
        "human_review_required": review_required,
        "exo_workflow_present": workflow_present,
        "main_rulesets": [rule.get("name") for rule in main_rulesets],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", action="append", help="Audit only this owner/repo")
    parser.add_argument("--strict", action="store_true", help="Exit 1 on any missing control")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    args = parser.parse_args()

    data = yaml.safe_load(MANIFEST.read_text())
    entries = data["repositories"]
    if args.repo:
        entries = [entry for entry in entries if entry["github_repo"] in args.repo]

    # GitHub API calls are independent per repository. Keep manifest order in
    # the report while parallelizing the network waits so fleet audits remain
    # usable as the portfolio grows.
    with ThreadPoolExecutor(max_workers=min(8, max(1, len(entries)))) as pool:
        reports = list(pool.map(lambda entry: audit(entry, data), entries))
    if args.json:
        print(json.dumps(reports, indent=2, ensure_ascii=False))
    else:
        print("repo\tprotected\treview\texo-ci\tmissing-adapters")
        for report in reports:
            print(
                "\t".join(
                    [
                        report["github_repo"],
                        "PASS" if report["main_protected"] else "FAIL",
                        "PASS" if report["human_review_required"] else "FAIL",
                        "PASS" if report["exo_workflow_present"] else "WARN",
                        ",".join(report["missing_adapters"]) or "-",
                    ]
                )
            )

    if not args.strict:
        return 0
    return int(
        any(
            report["missing_adapters"]
            or not report["main_protected"]
            or not report["human_review_required"]
            or not report["exo_workflow_present"]
            for report in reports
        )
    )


if __name__ == "__main__":
    sys.exit(main())
