"""GRAPH_DOGFOOD_RESUME_RUN_ID loads an existing Run without creating a Goal."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from agent_graph.durable_runtime import DurableGraphRuntime
from agent_graph.sqlite_store import SqliteControlPlaneStore

ROOT = Path(__file__).resolve().parents[1]
DOGFOOD = ROOT / "scripts" / "graph-schedule-realcodex-dogfood.py"


class ResumeRunIdTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.db = self.root / "control" / "g.sqlite"
        self.db.parent.mkdir(parents=True)
        self.worktree = self.root / "wt"
        self.worktree.mkdir()
        # Minimal git repo so attribution / branch helpers succeed.
        subprocess.run(["git", "init"], cwd=self.worktree, check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=self.worktree,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "test"],
            cwd=self.worktree,
            check=True,
            capture_output=True,
        )
        (self.worktree / "README").write_text("x\n", encoding="utf-8")
        subprocess.run(["git", "add", "README"], cwd=self.worktree, check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "init"],
            cwd=self.worktree,
            check=True,
            capture_output=True,
        )
        self.base = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=self.worktree, text=True
        ).strip()
        self.store = SqliteControlPlaneStore(str(self.db))
        self.rt = DurableGraphRuntime(self.store)
        self.run = self.rt.create_run(
            objective="Marker path: docs/agent-graph/real-codex-e2e-marker-test.md\n",
            project="portfolio-ops",
            risk_tier="R1",
            success_condition="test",
            base_sha=self.base,
            worktree=str(self.worktree),
            branch="chore/test-resume",
            repository="jerry200176-png/portfolio-ops",
        )

    def tearDown(self) -> None:
        self.rt.close()
        self.tmp.cleanup()

    def test_validate_resume_only_loads_existing_run(self) -> None:
        env = os.environ.copy()
        env.update(
            {
                "GRAPH_REAL_CODEX": "1",
                "GRAPH_CONTROL_DB": str(self.db),
                "GRAPH_DOGFOOD_RESUME_RUN_ID": self.run.run_id,
                "GRAPH_DOGFOOD_VALIDATE_RESUME_ONLY": "1",
                "GRAPH_DOGFOOD_ROOT": str(self.root),
                "PATH": env.get("PATH", ""),
            }
        )
        # Avoid network / agent-start; attribution mutates local git config only.
        with mock.patch(
            "agent_graph.worktree_bind.ensure_github_attribution",
            return_value=None,
        ):
            # Patch is inside the script's import path — call script with patched module via env
            pass
        proc = subprocess.run(
            [sys.executable, str(DOGFOOD)],
            cwd=str(ROOT),
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr + proc.stdout)
        # Last JSON line on stdout
        lines = [ln for ln in proc.stdout.splitlines() if ln.strip().startswith("{")]
        self.assertTrue(lines, msg=proc.stdout)
        payload = json.loads(lines[-1])
        self.assertTrue(payload["ok"])
        self.assertTrue(payload["resumed"])
        self.assertEqual(payload["run_id"], self.run.run_id)
        self.assertIn("real-codex-e2e-marker-test.md", payload["marker"])

    def test_validate_resume_missing_run_fails(self) -> None:
        env = os.environ.copy()
        env.update(
            {
                "GRAPH_REAL_CODEX": "1",
                "GRAPH_CONTROL_DB": str(self.db),
                "GRAPH_DOGFOOD_RESUME_RUN_ID": "run_does_not_exist",
                "GRAPH_DOGFOOD_VALIDATE_RESUME_ONLY": "1",
                "GRAPH_DOGFOOD_ROOT": str(self.root),
            }
        )
        proc = subprocess.run(
            [sys.executable, str(DOGFOOD)],
            cwd=str(ROOT),
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 1)
        self.assertIn("not found", proc.stderr)


if __name__ == "__main__":
    unittest.main()
