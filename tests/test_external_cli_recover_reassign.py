"""Dead worker → observe → reclaim → external_cli restep (no Founder)."""

from __future__ import annotations

import os
import signal
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

from agent_graph.canonical_paths import worktree_resource_key
from agent_graph.durable_runtime import DurableGraphRuntime
from agent_graph.external_cli_adapter import ExternalCliWorkerAdapter, build_stub_command
from agent_graph.harness import GraphHarness
from agent_graph.process_identity import read_process_identity
from agent_graph.sqlite_store import SqliteControlPlaneStore

STUB = Path(__file__).resolve().parent.parent / "scripts" / "graph-external-cli-stub-worker.py"


class ExternalCliRecoverReassignTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.db = self.root / "cp" / "graph.sqlite"
        self.db.parent.mkdir(parents=True)
        self.worktree = self.root / "wt"
        self.worktree.mkdir()
        (self.worktree / ".git").mkdir()
        self.store = SqliteControlPlaneStore(str(self.db))
        self.rt = DurableGraphRuntime(self.store)
        self.harness = GraphHarness(self.rt)
        self.base = "a" * 40
        self._pgids: list[int] = []

    def tearDown(self) -> None:
        for pgid in list(self._pgids):
            try:
                os.killpg(pgid, signal.SIGKILL)
            except OSError:
                pass
            try:
                os.waitpid(-pgid, os.WNOHANG)
            except OSError:
                pass
        self._pgids.clear()
        self.rt.close()
        self.tmp.cleanup()

    def _stub_worker(self) -> ExternalCliWorkerAdapter:
        return ExternalCliWorkerAdapter(
            provider_id="stub",
            command_builder=lambda wt, prompt, ctx: build_stub_command(
                wt, prompt, {**ctx, "stub_bin": str(STUB)}
            ),
            timeout_sec=30.0,
            canonical_db_path=self.db,
        )

    def test_alive_prior_worker_waits_without_founder(self) -> None:
        run = self.rt.create_run(
            objective="wait alive",
            project="portfolio-ops",
            base_sha=self.base,
            worktree=str(self.worktree),
            branch="t",
        )
        resource = worktree_resource_key(str(self.worktree))
        child = subprocess.Popen(
            ["bash", "-c", "while true; do sleep 1; done"],
            start_new_session=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        self._pgids.append(child.pid)
        identity = None
        deadline = time.time() + 5
        while time.time() < deadline:
            identity = read_process_identity(child.pid)
            if identity is not None:
                break
            time.sleep(0.05)
        self.assertIsNotNone(identity)

        now = "2026-09-17T10:00:00Z"
        a = self.rt.start_attempt(run.run_id, worker_type="external_cli")
        with self.store.transaction() as conn:
            token = self.store.acquire_execution_lease(
                resource_key=resource,
                attempt_id=a.attempt_id,
                run_id=run.run_id,
                node=a.node,
                now=now,
                expires_at="2099-01-01T00:00:00Z",
                lease_id="lease_alive",
                conn=conn,
            )
            self.store.bind_execution_identity(
                resource_key=resource,
                attempt_id=a.attempt_id,
                fencing_token=token,
                identity=identity,
                conn=conn,
            )

        out = self.harness.recover_and_step(
            run.run_id,
            worker=self._stub_worker(),
            model_profile="external_cli:stub",
            extra_context={"CANONICAL_DB_PATH": str(self.db)},
        )
        self.assertFalse(out["accepted"])
        self.assertEqual(out["action"], "wait_prior_worker_alive")
        self.assertFalse(out["founder_required"])
        self.assertEqual(self.rt.get_run(run.run_id).current_node, "investigator")

    def test_dead_prior_worker_reclaim_and_restep(self) -> None:
        run = self.rt.create_run(
            objective="reclaim dead",
            project="portfolio-ops",
            base_sha=self.base,
            worktree=str(self.worktree),
            branch="t",
        )
        resource = worktree_resource_key(str(self.worktree))
        child = subprocess.Popen(
            ["bash", "-c", "while true; do sleep 1; done"],
            start_new_session=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        self._pgids.append(child.pid)
        identity = None
        deadline = time.time() + 5
        while time.time() < deadline:
            identity = read_process_identity(child.pid)
            if identity is not None:
                break
            time.sleep(0.05)
        self.assertIsNotNone(identity)

        now = "2026-09-17T10:00:00Z"
        a = self.rt.start_attempt(run.run_id, worker_type="external_cli")
        with self.store.transaction() as conn:
            token = self.store.acquire_execution_lease(
                resource_key=resource,
                attempt_id=a.attempt_id,
                run_id=run.run_id,
                node=a.node,
                now=now,
                expires_at="2099-01-01T00:00:00Z",
                lease_id="lease_dead",
                conn=conn,
            )
            a.fencing_token = token
            self.store.update_attempt(a, conn=conn)
            self.store.bind_execution_identity(
                resource_key=resource,
                attempt_id=a.attempt_id,
                fencing_token=token,
                identity=identity,
                conn=conn,
            )

        os.kill(child.pid, signal.SIGKILL)
        child.wait(timeout=5)
        self._pgids = [p for p in self._pgids if p != child.pid]
        deadline = time.time() + 5
        while time.time() < deadline and Path(f"/proc/{child.pid}").exists():
            time.sleep(0.05)

        obs = self.harness.observe_worktree_lease(run.run_id)
        self.assertEqual(obs["liveness"], "dead")
        self.assertEqual(obs["recovery"], "reclaim_and_step")
        self.assertFalse(obs["founder_required"])

        out = self.harness.recover_and_step(
            run.run_id,
            worker=self._stub_worker(),
            model_profile="external_cli:stub",
            extra_context={"CANONICAL_DB_PATH": str(self.db)},
        )
        self.assertTrue(out["accepted"], out)
        self.assertEqual(out["action"], "reclaim_and_step")
        self.assertFalse(out["founder_required"])
        after = self.rt.get_run(run.run_id)
        self.assertEqual(after.current_node, "builder")
        orphaned = self.store.get_attempt(a.attempt_id)
        self.assertIsNotNone(orphaned)
        self.assertEqual(orphaned.status, "orphaned")


if __name__ == "__main__":
    unittest.main()
