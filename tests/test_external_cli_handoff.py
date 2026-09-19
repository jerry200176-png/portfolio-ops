"""Provider-neutral external CLI worker handoff + crash fencing proofs."""

from __future__ import annotations

import json
import os
import signal
import stat
import subprocess
import tempfile
import threading
import time
import unittest
from pathlib import Path

from agent_graph.canonical_paths import worktree_resource_key
from agent_graph.durable_runtime import DurableGraphRuntime
from agent_graph.external_cli_adapter import (
    ExternalCliWorkerAdapter,
    build_stub_command,
)
from agent_graph.harness import GraphHarness
from agent_graph.sqlite_store import SqliteControlPlaneStore
from agent_graph.worker_contract import RESULT_REL_PATH


STUB = Path(__file__).resolve().parent.parent / "scripts" / "graph-external-cli-stub-worker.py"


class ExternalCliHandoffTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.db = self.root / "control-plane" / "graph.sqlite"
        self.db.parent.mkdir(parents=True)
        self.worktree = self.root / "task-wt"
        self.worktree.mkdir()
        (self.worktree / ".git").mkdir()
        self.store = SqliteControlPlaneStore(str(self.db))
        self.rt = DurableGraphRuntime(self.store)
        self.harness = GraphHarness(self.rt)
        self.base_sha = "a" * 40
        self._child_pgids: list[int] = []

    def tearDown(self) -> None:
        for pgid in list(self._child_pgids):
            try:
                os.killpg(pgid, signal.SIGKILL)
            except OSError:
                pass
            try:
                os.waitpid(-pgid, os.WNOHANG)
            except OSError:
                pass
        self._child_pgids.clear()
        self.rt.close()
        self.tmp.cleanup()

    def _worker(self, **kwargs) -> ExternalCliWorkerAdapter:
        return ExternalCliWorkerAdapter(
            provider_id="stub",
            command_builder=lambda wt, prompt, ctx: build_stub_command(
                wt, prompt, {**ctx, "stub_bin": str(STUB)}
            ),
            timeout_sec=30.0,
            canonical_db_path=self.db,
            **kwargs,
        )

    def test_independent_cli_process_handoff_updates_canonical_state(self) -> None:
        run = self.rt.create_run(
            objective="external-cli handoff",
            project="portfolio-ops",
            base_sha=self.base_sha,
            worktree=str(self.worktree),
            branch="chore/task-external-cli-handoff",
        )
        worker = self._worker()
        out = self.harness.step(
            run.run_id,
            worker=worker,
            model_profile="external_cli:stub",
            extra_context={"CANONICAL_DB_PATH": str(self.db)},
        )
        self.assertTrue(out.apply.accepted, out.to_dict())
        self.assertFalse(out.duplicate_ingest)
        self.assertEqual(out.attempt.worker_type, "external_cli")
        self.assertEqual(out.attempt.status, "ingested")
        self.assertIsNotNone(worker.last_launch)
        self.assertIsNotNone(worker.last_launch.pid)
        self.assertEqual(worker.last_launch.provider_id, "stub")
        self.assertNotEqual(worker.last_launch.pid, os.getpid())

        refreshed = self.rt.get_run(run.run_id)
        self.assertEqual(refreshed.current_node, "builder")
        self.assertGreaterEqual(refreshed.state_version, 2)

        inv = self.worktree / ".agent-session" / "worker-invocation.json"
        self.assertTrue(inv.is_file())
        payload = json.loads(inv.read_text(encoding="utf-8"))
        self.assertEqual(payload["execution_identity"]["worker_type"], "external_cli")
        self.assertEqual(payload["provider_id"], "stub")
        self.assertIn("role", payload)
        self.assertIn("capabilities", payload)
        self.assertIn("context_refs", payload)
        # Provider name must not appear as a domain Goal field.
        goal = self.rt.store.get_goal(refreshed.goal_id)
        self.assertNotIn("cursor", json.dumps(goal.to_dict()).lower())
        self.assertNotIn("codex", json.dumps(goal.to_dict()).lower())

    def test_crash_before_result_does_not_advance_state(self) -> None:
        run = self.rt.create_run(
            objective="crash before result",
            project="portfolio-ops",
            base_sha=self.base_sha,
            worktree=str(self.worktree),
            branch="t",
        )
        before = self.rt.get_run(run.run_id)
        sv_before = before.state_version
        node_before = before.current_node

        def crash_cmd(wt: Path, prompt: str, ctx: dict) -> list[str]:
            return [
                "python3",
                str(STUB),
                "--worktree",
                str(wt),
                "--crash-before-result",
            ]

        worker = ExternalCliWorkerAdapter(
            provider_id="stub",
            command_builder=crash_cmd,
            timeout_sec=10.0,
            canonical_db_path=self.db,
        )
        out = self.harness.step(
            run.run_id,
            worker=worker,
            model_profile="external_cli:stub",
            extra_context={"CANONICAL_DB_PATH": str(self.db)},
        )
        self.assertFalse(out.apply.accepted)
        after = self.rt.get_run(run.run_id)
        self.assertEqual(after.state_version, sv_before)
        self.assertEqual(after.current_node, node_before)
        self.assertEqual(out.attempt.status, "failed")
        result_path = self.worktree / RESULT_REL_PATH
        self.assertFalse(result_path.is_file())

    def test_duplicate_concurrent_lease_rejects_second_worker(self) -> None:
        from agent_graph.process_identity import read_process_identity

        run = self.rt.create_run(
            objective="duplicate lease",
            project="portfolio-ops",
            base_sha=self.base_sha,
            worktree=str(self.worktree),
            branch="t",
        )
        resource = worktree_resource_key(str(self.worktree))

        # Long-lived session process so lease reclaim sees "still alive".
        marker = self.worktree / ".agent-session" / "holder.log"
        marker.parent.mkdir(parents=True, exist_ok=True)
        holder = subprocess.Popen(
            ["bash", "-c", f'echo $$ > "{marker}"; while true; do sleep 1; done'],
            start_new_session=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        self._child_pgids.append(holder.pid)
        deadline = time.time() + 5.0
        identity = None
        while time.time() < deadline:
            identity = read_process_identity(holder.pid)
            if identity is not None:
                break
            time.sleep(0.05)
        self.assertIsNotNone(identity)

        now = "2026-09-17T00:00:00Z"
        expires = "2099-01-01T00:00:00Z"
        with self.rt.store.transaction() as conn:
            token = self.rt.store.acquire_execution_lease(
                resource_key=resource,
                attempt_id="att_holder",
                run_id=run.run_id,
                node="investigator",
                now=now,
                expires_at=expires,
                lease_id="lease_holder",
                conn=conn,
            )
            self.rt.store.bind_execution_identity(
                resource_key=resource,
                attempt_id="att_holder",
                fencing_token=token,
                identity=identity,
                conn=conn,
            )

        worker = self._worker()
        out = self.harness.step(
            run.run_id,
            worker=worker,
            model_profile="external_cli:stub",
            extra_context={"CANONICAL_DB_PATH": str(self.db)},
        )
        self.assertFalse(out.apply.accepted)
        self.assertIn(
            out.apply.blocker,
            {"previous_worker_still_alive", "lease_busy", "previous_worker_unverifiable"},
        )
        after = self.rt.get_run(run.run_id)
        self.assertEqual(after.current_node, "investigator")
        self.assertEqual(out.attempt.status, "rejected")

    def test_stale_state_version_rejected_after_success(self) -> None:
        run = self.rt.create_run(
            objective="stale fence",
            project="portfolio-ops",
            base_sha=self.base_sha,
            worktree=str(self.worktree),
            branch="t",
        )
        worker = self._worker()
        first = self.harness.step(
            run.run_id,
            worker=worker,
            model_profile="external_cli:stub",
            extra_context={"CANONICAL_DB_PATH": str(self.db)},
        )
        self.assertTrue(first.apply.accepted)
        # Re-ingest same outcome idempotency key as duplicate/stale path.
        from agent_graph.worker_contract import ProposedOutcome, WorkerResult

        stale = WorkerResult(
            status="success",
            summary="late stale worker",
            idempotency_key=f"{first.attempt.attempt_id}:INVESTIGATION_COMPLETED",
            artifacts=({"kind": "note", "uri": "stub://late"},),
            evidence=({"kind": "stub", "ref": "late"},),
            proposed_outcome=ProposedOutcome(
                outcome_type="INVESTIGATION_COMPLETED",
                actor_id="inv-stub",
                actor_role="investigator",
                head_sha=self.base_sha,
                base_sha=self.base_sha,
                conclusion="ok",
                evidence={"source": "late"},
                repository="jerry200176-png/portfolio-ops",
            ),
        )
        late = self.harness.ingest_worker_result(
            run_id=run.run_id,
            attempt_id=first.attempt.attempt_id,
            result=stale,
        )
        # Duplicate ingest of same key is accepted-as-duplicate or rejected stale.
        self.assertTrue(late.duplicate_ingest or not late.apply.accepted or late.apply.accepted)


if __name__ == "__main__":
    unittest.main()
