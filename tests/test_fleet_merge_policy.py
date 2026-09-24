from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class FleetMergePolicyTests(unittest.TestCase):
    def test_autonomy_agent_is_operator(self):
        policy = (ROOT / "governance/AUTONOMY_POLICY.md").read_text(
            encoding="utf-8"
        )
        fleet = (ROOT / "docs/fleet-merge-policy.md").read_text(encoding="utf-8")
        contract = (ROOT / "governance/company-agent-contract.yaml").read_text(
            encoding="utf-8"
        )
        self.assertIn("docs/fleet-merge-policy.md", policy)
        self.assertIn("Deploy itself is not a Founder gate", policy)
        self.assertIn("Merge a low-risk reversible PR", policy)
        self.assertIn("**Yes**", policy.split("Merge a low-risk reversible PR")[1][:240])
        self.assertIn("Production **data** mutation", policy)
        self.assertIn("Conditional", policy.split("Production **data** mutation")[1][:120])
        self.assertIn("backup/recovery point", policy.split("Production **data** mutation")[1][:180])
        self.assertIn("Controlled R3 execution", policy)
        self.assertIn("Stop if recovery or", fleet)
        self.assertIn("Close a GitHub issue", policy)
        self.assertIn("Gmail trash / delete", policy)
        self.assertIn("**No**", policy.split("Gmail trash / delete")[1][:120])
        self.assertIn("gh pr merge --squash --delete-branch", fleet)
        self.assertIn("Do not `--admin`", fleet)
        self.assertIn("r0_r1_r2_squash_merge", contract)
        self.assertIn("controlled_r3_execution_via_product_path", contract)
        self.assertIn("founder_approval_required", contract)
        self.assertIn("machine_banned", contract)
        self.assertIn("required_status_checks_before_merge", contract)
        self.assertIn("weaken_tests_assertions_allowlists_or_security_controls", contract)
        settings = (ROOT / ".claude/settings.json").read_text(encoding="utf-8")
        self.assertNotIn("merge_pull_request", settings)
        self.assertNotIn("send_message", settings)
        self.assertIn("delete_message", settings)


if __name__ == "__main__":
    unittest.main()
