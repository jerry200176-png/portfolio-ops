import json
import os
import subprocess
import tempfile
import unittest

STATUS_SCRIPT = "/home/jerry/workspace/agent-control/bin/agent-status"
FINISH_SCRIPT = "/home/jerry/workspace/agent-control/bin/agent-finish"
START_SCRIPT = "/home/jerry/workspace/agent-control/bin/agent-start"

class TestAgentLifecycle(unittest.TestCase):
    def test_scripts_exist_and_executable(self):
        for script in [STATUS_SCRIPT, FINISH_SCRIPT, START_SCRIPT]:
            self.assertTrue(os.path.isfile(script), f"Missing {script}")
            self.assertTrue(os.access(script, os.X_OK), f"Not executable: {script}")

    def test_agent_status_help(self):
        res = subprocess.run([STATUS_SCRIPT, "--help"], text=True, capture_output=True)
        self.assertEqual(res.returncode, 0)
        self.assertIn("Inspect task lifecycle", res.stdout)

    def test_disposable_path_classification(self):
        # Import agent-status as module to test path classifier directly
        import importlib.util
        import importlib.machinery
        loader = importlib.machinery.SourceFileLoader("agent_status_mod", STATUS_SCRIPT)
        spec = importlib.util.spec_from_loader("agent_status_mod", loader)
        mod = importlib.util.module_from_spec(spec)
        loader.exec_module(mod)

        # Disposables
        self.assertTrue(mod.is_disposable_path(".agent-session/manifest.json"))
        self.assertTrue(mod.is_disposable_path(".exo/cache/sessions/human.active.json"))
        self.assertTrue(mod.is_disposable_path(".exo/locks/fencing.json"))
        self.assertTrue(mod.is_disposable_path("out/xindian-capacity.model.json"))
        self.assertTrue(mod.is_disposable_path("docs/analysis/some_notes.md"))
        self.assertTrue(mod.is_disposable_path(".cursor/plans/my-plan.md"))
        self.assertTrue(mod.is_disposable_path("debug.log"))
        self.assertTrue(mod.is_disposable_path(".pytest_cache/v/cache"))

        # Product files (MUST NOT be disposable!)
        self.assertFalse(mod.is_disposable_path("backend/app/Models/User.php"))
        self.assertFalse(mod.is_disposable_path("frontend/src/App.vue"))
        self.assertFalse(mod.is_disposable_path("config/database.php"))
        self.assertFalse(mod.is_disposable_path(".github/workflows/deploy.yml"))
        self.assertFalse(mod.is_disposable_path("scripts/agent-preflight.sh"))

    def test_agent_status_all_alltrue(self):
        # Run agent-status alltrue --all and verify output structure
        res = subprocess.run([STATUS_SCRIPT, "alltrue", "--all"], text=True, capture_output=True)
        self.assertEqual(res.returncode, 0)
        self.assertIn("Fleet Task Worktrees for Project [alltrue]", res.stdout)
        self.assertIn("TASK ID", res.stdout)
        self.assertIn("STAGE", res.stdout)
        self.assertIn("Summary:", res.stdout)

    def test_lifecycle_stages_consistency(self):
        expected_stages = [
            "NOT_STARTED",
            "IMPLEMENTED",
            "TESTED",
            "PR_OPENED",
            "MERGED",
            "DEPLOYED",
            "PRODUCTION_VERIFIED"
        ]
        self.assertEqual(len(expected_stages), 7)

        # Check COMMANDER_WORKER_VERIFIER.md
        verifier_doc = "/home/jerry/workspace/portfolio-ops/governance/COMMANDER_WORKER_VERIFIER.md"
        with open(verifier_doc, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("7 階標準生命週期", content)
        for stage in expected_stages:
            self.assertIn(f"[{stage}]", content)

        # Check AGENT_BOOTSTRAP.md
        bootstrap_doc = "/home/jerry/workspace/portfolio-ops/governance/AGENT_BOOTSTRAP.md"
        with open(bootstrap_doc, "r", encoding="utf-8") as f:
            b_content = f.read()
        self.assertIn("7-stage lifecycle", b_content)
        normalized = " ".join(b_content.split())
        self.assertIn("`not_started` -> `implemented` -> `tested` -> `pr_opened` -> `merged` -> `deployed` -> `production_verified`", normalized)

if __name__ == "__main__":
    unittest.main()
