from pathlib import Path
import importlib.util
import re
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]


def load_ruleset_module():
    path = ROOT / "scripts" / "apply-github-baseline-rulesets.py"
    spec = importlib.util.spec_from_file_location("apply_rulesets", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class GovernanceBaselineTests(unittest.TestCase):
    def test_company_health_files_exist(self):
        for path in (
            "CONTRIBUTING.md",
            "CODE_OF_CONDUCT.md",
            "SECURITY.md",
            ".github/CODEOWNERS",
            ".github/PULL_REQUEST_TEMPLATE.md",
            ".github/ISSUE_TEMPLATE/config.yml",
            ".github/ISSUE_TEMPLATE/bug.yml",
            ".github/ISSUE_TEMPLATE/decision.yml",
            ".github/dependabot.yml",
        ):
            self.assertTrue((ROOT / path).is_file(), path)

    def test_workspace_manifest_names_required_control_plane_paths(self):
        manifest = (ROOT / "workspace.manifest.yaml").read_text(encoding="utf-8")
        for name in (
            "bare_repos",
            "canonical_checkouts",
            "active_worktrees",
            "tasks",
            "archives",
            "evidence",
            "backups",
            "agent_control",
            "control_plane",
        ):
            self.assertIn(f"  {name}:", manifest)

    def test_scripts_are_proposal_safe(self):
        scripts = "\n".join(
            (ROOT / "scripts" / name).read_text(encoding="utf-8")
            for name in (
                "phase1-inventory-backup.sh",
                "phase2-fetch-only.sh",
                "phase3-cleanup-proposal.sh",
                "workspace-inventory.sh",
                "github-governance-audit.sh",
            )
        )
        for command in ("git reset", "git clean", "git merge", "git rebase", "git worktree remove", "git worktree prune"):
            self.assertNotRegex(scripts, rf"(?m)^\s*{re.escape(command)}\b")
        self.assertNotRegex(scripts, r"(?m)^\s*(rm|mv)\s")
        self.assertIn("git -C \"$repo\" fetch --no-tags origin", scripts)
        self.assertIn("Read-only", scripts)

    def test_ci_has_least_privilege_baseline(self):
        ci = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
        security = (ROOT / ".github/workflows/security.yml").read_text(encoding="utf-8")
        self.assertIn("contents: read", ci)
        self.assertIn("contents: read", security)
        self.assertIn("gitleaks/gitleaks-action", security)
        self.assertIn("github/codeql-action", security)
        self.assertIn("ossf/scorecard-action@", security)
        self.assertIn("step-security/harden-runner@", security)
        self.assertNotIn("actions/checkout@v", ci + security)

    def test_component_contracts_exist(self):
        for name in ("alltrue.yaml", "sunrise.yaml", "portfolio-ops.yaml"):
            self.assertTrue((ROOT / "catalog" / name).is_file(), name)

    def test_portfolio_evidence_contract_is_minimal_and_read_only(self):
        contract = (ROOT / "governance" / "portfolio-evidence-contract.yaml").read_text(encoding="utf-8")
        self.assertIn("contract_id: portfolio-evidence-envelope-v1", contract)
        self.assertIn("repository: engineering-intelligence", contract)
        self.assertIn("central_etl: false", contract)
        self.assertIn("central_database: false", contract)
        self.assertIn("stale_actions: proposal_only", contract)
        for field in ("persona", "primary_cta", "loading_state", "error_state", "empty_state", "accessibility", "mobile_behavior", "cognitive_load_notes"):
            self.assertIn(f"    - {field}", contract)

    def test_governance_contract_validator_passes(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts/validate-governance-contract.py")],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_existing_ruleset_drift_is_blocked_by_default(self):
        module = load_ruleset_module()
        desired = module.payload()
        self.assertEqual(desired["rules"][2]["parameters"]["required_approving_review_count"], 0)
        self.assertFalse(desired["rules"][2]["parameters"]["require_last_push_approval"])
        self.assertFalse(desired["rules"][2]["parameters"]["required_review_thread_resolution"])
        drifted = {**desired, "rules": [{"type": "deletion"}]}
        self.assertEqual(module.existing_action(drifted, desired, False), "blocked")
        self.assertEqual(module.existing_action(drifted, desired, True), "updated")
        self.assertEqual(module.existing_action(desired, desired, False), "unchanged")

    def test_remote_governance_policy_does_not_require_human_review(self):
        policy = (ROOT / "governance" / "repository-governance.yaml").read_text(encoding="utf-8")
        self.assertIn("require_human_review: false", policy)


if __name__ == "__main__":
    unittest.main()
