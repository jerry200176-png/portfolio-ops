from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class FleetMergePolicyTests(unittest.TestCase):
    def test_autonomy_allows_r0_r2_merge_not_r3_or_gmail(self):
        policy = (ROOT / "governance/AUTONOMY_POLICY.md").read_text(
            encoding="utf-8"
        )
        fleet = (ROOT / "docs/fleet-merge-policy.md").read_text(encoding="utf-8")
        contract = (ROOT / "governance/company-agent-contract.yaml").read_text(
            encoding="utf-8"
        )
        self.assertIn("docs/fleet-merge-policy.md", policy)
        self.assertRegex(policy, r"Merge a pull request \(R0–R2\).*\*\*Yes\*\*")
        self.assertRegex(policy, r"Merge a pull request \(R3\).*\*\*No\*\*")
        self.assertIn("Send email", policy)
        self.assertIn("**No**", policy.split("Send email")[1][:200])
        self.assertIn("gh pr merge --squash --delete-branch", fleet)
        self.assertIn("Do not `--admin`", fleet)
        self.assertIn("r0_r1_r2_squash_merge", contract)
        self.assertNotIn("- merge\n", contract)
        self.assertIn("required_status_checks_before_merge", contract)
        self.assertNotIn("independent_human_review_required", contract)
        settings = (ROOT / ".claude/settings.json").read_text(encoding="utf-8")
        self.assertNotIn("merge_pull_request", settings)


if __name__ == "__main__":
    unittest.main()
