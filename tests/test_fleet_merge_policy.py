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
        self.assertRegex(policy, r"Merge a pull request \(R0–R3\).*\*\*Yes\*\*")
        self.assertIn("Close a GitHub issue", policy)
        self.assertIn("Send or reply on Gmail", policy)
        self.assertIn("**Yes**", policy.split("Send or reply on Gmail")[1][:240])
        self.assertIn("Gmail trash / delete", policy)
        self.assertIn("**No**", policy.split("Gmail trash / delete")[1][:120])
        self.assertIn("gh pr merge --squash --delete-branch", fleet)
        self.assertIn("Do not `--admin`", fleet)
        self.assertIn("r0_r1_r2_r3_squash_merge", contract)
        self.assertIn("machine_banned", contract)
        self.assertNotIn("founder_approval_required", contract)
        self.assertIn("required_status_checks_before_merge", contract)
        settings = (ROOT / ".claude/settings.json").read_text(encoding="utf-8")
        self.assertNotIn("merge_pull_request", settings)
        self.assertNotIn("send_message", settings)
        self.assertIn("delete_message", settings)


if __name__ == "__main__":
    unittest.main()
