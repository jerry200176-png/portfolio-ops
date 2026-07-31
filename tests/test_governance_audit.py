from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class GovernanceAuditTests(unittest.TestCase):
    def test_audit_script_is_read_only_in_intent(self):
        script = (ROOT / "scripts/portfolio-governance-audit.sh").read_text()
        self.assertIn("git -C \"$repo\" status", script)
        self.assertIn("git -C \"$repo\" remote get-url", script)
        self.assertNotIn("git reset", script)
        self.assertNotIn("git clean", script)
        self.assertNotIn("git worktree remove", script)
        self.assertNotIn("git worktree prune", script)
        self.assertNotIn("rm ", script)
        self.assertNotIn("mv ", script)


if __name__ == "__main__":
    unittest.main()
