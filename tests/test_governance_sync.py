from pathlib import Path
import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("sync_governance", ROOT / "scripts/sync-governance.py")
sync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync)


class GovernanceSyncTests(unittest.TestCase):
    def test_targets_follow_registry_flag(self):
        with tempfile.TemporaryDirectory() as tmp:
            reg = Path(tmp) / "p.yaml"
            reg.write_text(yaml.safe_dump({"projects": [
                {"id": "a", "github_repo": "o/a", "governance_sync": True},
                {"id": "b", "github_repo": "o/b", "governance_sync": False},
                {"id": "c", "github_repo": "o/c"},
                {"id": "d", "github_repo": None, "governance_sync": True}]}))
            self.assertEqual(sync.targets(reg), ["o/a"])
            self.assertEqual(sync.targets(reg, only="o/z"), [])

    def test_real_registry_syncs_products_and_never_retired_repos(self):
        repos = sync.targets(ROOT / "portfolio.yaml")
        self.assertIn("jerry200176-png/sunrise-cafe", repos)
        self.assertNotIn("jerry200176-png/exoprotocol", repos)
        self.assertNotIn("jerry200176-png/portfolio-ops", repos)

    def test_skips_cleanly_without_token(self):
        env = {k: v for k, v in os.environ.items() if k not in ("GOVERNANCE_SYNC_TOKEN", "GH_TOKEN")}
        res = subprocess.run([sys.executable, str(ROOT / "scripts/sync-governance.py"), "--sha", "a" * 40],
                             capture_output=True, text=True, env=env)
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertIn("skipping", res.stdout)

    def test_synced_files_exist_and_workflows_are_wired(self):
        for rel in sync.SYNC_FILES + [sync.TEMPLATE_SRC, "governance/templates/AGENTS.skeleton.md"]:
            self.assertTrue((ROOT / rel).is_file(), rel)
        reusable = (ROOT / ".github/workflows/rulebook-check.yml").read_text(encoding="utf-8")
        self.assertIn("workflow_call:", reusable)
        wf = (ROOT / ".github/workflows/rulebook-sync.yml").read_text(encoding="utf-8")
        self.assertIn("GOVERNANCE_SYNC_TOKEN", wf)
        self.assertIn("skipping sync", wf)
        caller = (ROOT / "governance/templates/rulebook-check-caller.yml").read_text(encoding="utf-8")
        self.assertIn("rulebook-check.yml@__PORTFOLIO_OPS_SHA__", caller)
        skeleton = (ROOT / "governance/templates/AGENTS.skeleton.md").read_text(encoding="utf-8")
        for needle in ("read `governance/RULEBOOK.md`", "F1–F4", "D0", "D2/D3"):
            self.assertIn(needle, skeleton)


if __name__ == "__main__":
    unittest.main()
