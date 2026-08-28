from __future__ import annotations

import json
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "governance-autopilot.sh"
POLICY = ROOT / "governance" / "autonomy-automation.yaml"


class GovernanceAutopilotTests(unittest.TestCase):
    def run_autopilot(self, inventory: str) -> dict:
        with tempfile.TemporaryDirectory(prefix="governance-autopilot-test-") as directory:
            root = Path(directory)
            inventory_path = root / "inventory.tsv"
            output_path = root / "report.json"
            inventory_path.write_text(inventory, encoding="utf-8")
            result = subprocess.run(
                [
                    str(SCRIPT),
                    "--policy",
                    str(POLICY),
                    "--inventory",
                    str(inventory_path),
                    "--output",
                    str(output_path),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            return json.loads(output_path.read_text(encoding="utf-8"))

    def test_clean_rows_are_observed_and_dirty_rows_are_escalated(self):
        inventory = (
            "candidate\tgit_top\trole\tstatus\n"
            "/workspace/clean\t/workspace/clean\tcanonical-checkout\tclean\n"
            "/workspace/dirty\t/workspace/dirty\tactive-worktree\tdirty\n"
            "/workspace/orphan\t\tunresolved\tunreadable\n"
        )
        report = self.run_autopilot(inventory)

        self.assertEqual(report["summary"]["total_rows"], 3)
        self.assertEqual(report["summary"]["clean_rows"], 1)
        self.assertEqual(report["summary"]["approval_required_rows"], 2)
        self.assertEqual(len(report["approval_queue"]), 2)
        self.assertTrue(all(item["owner"] == "founder" for item in report["approval_queue"]))
        self.assertTrue(all(item["recovery"] for item in report["approval_queue"]))

    def test_malformed_rows_are_never_treated_as_safe(self):
        report = self.run_autopilot(
            "candidate\tgit_top\trole\tstatus\n"
            "/workspace/clean\t/workspace/clean\tcanonical-checkout\tclean\n"
            "/workspace/broken\t/workspace/broken\tclean\n"
        )

        self.assertEqual(report["summary"]["malformed_rows"], 1)
        self.assertEqual(report["summary"]["approval_required_rows"], 1)
        self.assertIn("malformed inventory row width", report["approval_queue"][0]["reason"])

    def test_default_mode_does_not_clean_without_explicit_owned_runtime(self):
        report = self.run_autopilot(
            "candidate\tgit_top\trole\tstatus\n"
            "/workspace/clean\t/workspace/clean\tcanonical-checkout\tclean\n"
        )
        self.assertIn(report["safe_cleanup"]["status"], {"not_present", "ownership_marker_missing", "clean"})

    def test_report_is_reproducible_except_for_timestamp(self):
        inventory = (
            "candidate\tgit_top\trole\tstatus\n"
            "/workspace/clean\t/workspace/clean\tcanonical-checkout\tclean\n"
        )
        first = self.run_autopilot(inventory)
        second = self.run_autopilot(inventory)
        first.pop("generated_at")
        second.pop("generated_at")
        first["source_inventory"] = "<inventory>"
        second["source_inventory"] = "<inventory>"
        self.assertEqual(first, second)
        self.assertRegex(first["source_inventory_sha256"], r"^[0-9a-f]{64}$")
        self.assertRegex(first["policy_sha256"], r"^[0-9a-f]{64}$")

    def test_script_contains_no_destructive_git_or_shell_cleanup_commands(self):
        source = SCRIPT.read_text(encoding="utf-8")
        for forbidden in ("git reset", "git clean", "git merge", "git rebase", "git push --force", "rm -rf", "\nmv "):
            self.assertNotIn(forbidden, source)
        self.assertIn("gio", source)
        self.assertIn("approval_queue", source)


if __name__ == "__main__":
    unittest.main()
