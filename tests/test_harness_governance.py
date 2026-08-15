from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class HarnessGovernanceTests(unittest.TestCase):
    def test_closeout_and_harness_keep_product_boundaries(self):
        closeout = (ROOT / "docs/session-closeout.md").read_text(encoding="utf-8")
        harness = (ROOT / "docs/small-project-harness.md").read_text(encoding="utf-8")
        lessons = (ROOT / "docs/HARD_LESSONS.md").read_text(encoding="utf-8")
        loop = (ROOT / "docs/agent-operating-loop.md").read_text(encoding="utf-8")
        for path in (
            "docs/session-closeout.md",
            "docs/small-project-harness.md",
            "docs/HARD_LESSONS.md",
            "docs/templates/session-journal.md",
        ):
            self.assertTrue((ROOT / path).is_file(), path)
        self.assertIn("docs/session-closeout.md", loop)
        self.assertIn("docs/small-project-harness.md", loop)
        self.assertIn("docs/HARD_LESSONS.md", loop)
        self.assertIn("never merges", closeout.lower())
        self.assertIn("AllTrue", harness)
        self.assertIn("Do not apply", harness)
        self.assertIn("Promotion", lessons)
        contract = (ROOT / "governance/company-agent-contract.yaml").read_text(
            encoding="utf-8"
        )
        self.assertIn("same_step_failures: 2", contract)
        self.assertIn("stall_minutes: 5", contract)
        self.assertNotRegex(closeout, r"(?i)agents? may merge")
        self.assertNotRegex(harness, r"(?i)autonomous deploy")


if __name__ == "__main__":
    unittest.main()
