#!/usr/bin/env python3
"""Validate the company-wide agent operating contract."""

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    path = ROOT / "governance/company-agent-contract.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    required = {
        "schema_version", "contract_id", "version", "maintainer_model",
        "control_plane", "agent_entrypoints", "session_invariants",
        "project_intake", "delivery_loop", "research_policy",
        "verification_policy", "learning_policy", "github_records",
    }
    missing = sorted(required - set(data))
    if missing:
        raise SystemExit(f"missing top-level keys: {', '.join(missing)}")
    if data["contract_id"] != "company-agent-operating-contract":
        raise SystemExit("unexpected contract_id")
    if data["maintainer_model"] != "single_owner":
        raise SystemExit("maintainer_model must be single_owner")
    invariants = data["session_invariants"]
    # draft_pr_is_default_finish_line may be false: low-risk work finishes at
    # merge/deploy/verify, not at Draft PR.
    required_true = [
        key
        for key in invariants
        if key not in {"production_mutation_default", "draft_pr_is_default_finish_line"}
    ]
    if any(invariants.get(key) is not True for key in required_true):
        raise SystemExit("all non-mutation session invariants must be true")
    if invariants.get("draft_pr_is_default_finish_line") not in (True, False):
        raise SystemExit("draft_pr_is_default_finish_line must be boolean")
    if invariants.get("production_mutation_default") is not False:
        raise SystemExit("production_mutation_default must be false")
    intake = data["project_intake"]
    for key in ("required_fields", "required_steps"):
        if not intake.get(key):
            raise SystemExit(f"project_intake.{key} is empty")
    phases = [row["id"] for row in data["delivery_loop"]["phases"]]
    if phases != ["discover", "research", "plan", "implement", "verify", "review", "learn"]:
        raise SystemExit(f"unexpected delivery loop: {phases}")
    sources = data["research_policy"]["minimum_source_classes"]
    if len(sources) < 3 or not data["research_policy"]["never_copy_code_without_license_and_fit_review"]:
        raise SystemExit("research policy is incomplete")
    required_checks = data["verification_policy"]["required_before_done"]
    for check in ("diff_check", "focused_tests", "secret_scan", "independent_evidence_review"):
        if check not in required_checks:
            raise SystemExit(f"verification policy missing {check}")
    print("PASS: company agent contract valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
