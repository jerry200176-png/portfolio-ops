from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class VerifyRetryLoopTests(unittest.TestCase):
    def test_sop_keeps_founder_gates_and_required_controls(self):
        sop = (ROOT / "docs/verify-retry-loop.md").read_text(encoding="utf-8")
        loop = (ROOT / "docs/agent-operating-loop.md").read_text(encoding="utf-8")
        record = ROOT / "docs/templates/verify-retry-record.md"
        self.assertTrue(record.is_file(), "verify-retry record template missing")
        self.assertIn("docs/verify-retry-loop.md", loop)
        for needle in (
            "## Eligibility",
            "## Generate / review split",
            "## Stop-loss",
            "Founder-gated",
            "captain-balung-blog.ghost.io/seven-stages-ai-agent-workflow",
            "docs/templates/verify-retry-record.md",
        ):
            self.assertIn(needle, sop)
        self.assertIn("merge", sop.lower())
        self.assertIn("deploy", sop.lower())
        self.assertNotRegex(
            sop,
            r"(?i)agents? may merge",
        )
        self.assertNotRegex(
            sop,
            r"(?i)autonomous deploy",
        )


if __name__ == "__main__":
    unittest.main()
