"""Tests for control-plane branch publish helper."""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from agent_graph.branch_push import BranchPushError, ensure_branch_pushed


class BranchPushTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.bare = self.root / "remote.git"
        self.wt = self.root / "work"
        subprocess.check_call(["git", "init", "--bare", str(self.bare)])
        subprocess.check_call(["git", "clone", str(self.bare), str(self.wt)])
        subprocess.check_call(
            ["git", "-C", str(self.wt), "config", "user.email", "t@example.com"]
        )
        subprocess.check_call(
            ["git", "-C", str(self.wt), "config", "user.name", "t"]
        )
        (self.wt / "README").write_text("a\n", encoding="utf-8")
        subprocess.check_call(["git", "-C", str(self.wt), "add", "README"])
        subprocess.check_call(["git", "-C", str(self.wt), "commit", "-m", "init"])
        # Default branch name may be master or main depending on git config.
        self.branch = subprocess.check_output(
            ["git", "-C", str(self.wt), "branch", "--show-current"], text=True
        ).strip()
        subprocess.check_call(
            ["git", "-C", str(self.wt), "push", "-u", "origin", "HEAD"]
        )

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_already_up_to_date(self) -> None:
        out = ensure_branch_pushed(self.wt)
        self.assertFalse(out["pushed"])
        self.assertTrue(out["already_up_to_date"])

    def test_push_new_commit(self) -> None:
        (self.wt / "README").write_text("b\n", encoding="utf-8")
        subprocess.check_call(["git", "-C", str(self.wt), "add", "README"])
        subprocess.check_call(["git", "-C", str(self.wt), "commit", "-m", "upd"])
        out = ensure_branch_pushed(self.wt)
        self.assertTrue(out["pushed"])
        head = subprocess.check_output(
            ["git", "-C", str(self.wt), "rev-parse", "HEAD"], text=True
        ).strip()
        remote = subprocess.check_output(
            ["git", "-C", str(self.bare), "rev-parse", self.branch], text=True
        ).strip()
        self.assertEqual(head, remote)

    def test_missing_worktree(self) -> None:
        with self.assertRaises(BranchPushError):
            ensure_branch_pushed(self.root / "nope")

    def test_scheduler_invokes_push_after_real_builder(self) -> None:
        from agent_graph.durable_runtime import DurableGraphRuntime
        from agent_graph.harness import FakeWorkerAdapter, GraphHarness
        from agent_graph.scheduler import GraphScheduler
        from agent_graph.sqlite_store import SqliteControlPlaneStore

        db = self.root / "g.sqlite"
        store = SqliteControlPlaneStore(str(db))
        rt = DurableGraphRuntime(store)
        harness = GraphHarness(rt)
        head = "b" * 40
        base = "a" * 40
        run = rt.create_run(
            objective="t",
            project="portfolio-ops",
            base_sha=base,
            worktree=str(self.wt),
            branch=self.branch,
        )
        # Advance investigator with fake worker under non-real path first.
        w = FakeWorkerAdapter(head_sha=head)
        self.assertTrue(harness.step(run.run_id, worker=w, write_context=False).apply.accepted)
        self.assertEqual(rt.get_run(run.run_id).current_node, "builder")

        sched = GraphScheduler(rt, head_sha=head, use_real_codex=True)
        with mock.patch(
            "agent_graph.branch_push.try_ensure_branch_pushed",
            return_value={"pushed": True, "branch": self.branch, "head_sha": head},
        ) as push_mock, mock.patch.object(
            sched, "_worker_for_run", return_value=FakeWorkerAdapter(head_sha=head)
        ):
            out = sched.tick(limit=1)
        self.assertTrue(any(x.get("branch_push") for x in out.advanced), out.advanced)
        push_mock.assert_called_once()
        rt.close()


if __name__ == "__main__":
    unittest.main()
