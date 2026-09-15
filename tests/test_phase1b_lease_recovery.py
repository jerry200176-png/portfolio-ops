"""Phase 1B lease recovery: expiry requires reconciliation, not takeover."""

from __future__ import annotations

import os
import signal
import stat
import subprocess
import tempfile
import textwrap
import time
import unittest
from pathlib import Path

from agent_graph.canonical_paths import worktree_resource_key
from agent_graph.durable_runtime import DurableGraphRuntime
from agent_graph.harness import GraphHarness
from agent_graph.process_identity import read_process_identity
from agent_graph.real_codex_adapter import RealCodexWorkerAdapter
from agent_graph.sqlite_store import (
    PreviousWorkerStillAliveError,
    PreviousWorkerUnverifiableError,
    SCHEMA_VERSION,
    SqliteControlPlaneStore,
)
from agent_graph.worker_contract import RESULT_REL_PATH


def _write_exec(path: Path, body: str) -> Path:
    path.write_text(body, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IEXEC)
    return path


ROUTE_DRY = (
    '{"profile":"terra","model":"stub","reasoning_effort_override":null,'
    '"reason":"t","resolution":"selected","requested_tier":"terra","selected_tier":"terra"}'
)


class Phase1BLeaseRecoveryTests(unittest.TestCase):
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
        self.bin = self.root / "bin"
        self.bin.mkdir()
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

    def _run(self):
        return self.rt.create_run(
            objective="lease-recovery",
            project="portfolio-ops",
            base_sha=self.base_sha,
            worktree=str(self.worktree),
            branch="t",
        )

    def _spawn_orphan_writer(self, marker: Path) -> subprocess.Popen:
        """Long-lived child in its own session (mirrors RealCodex start_new_session)."""
        marker.parent.mkdir(parents=True, exist_ok=True)
        proc = subprocess.Popen(
            [
                "bash",
                "-c",
                f'while true; do echo "writer-$(date +%s%N)" >> "{marker}"; sleep 0.15; done',
            ],
            start_new_session=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        self._child_pgids.append(proc.pid)
        # Wait until identity is readable and at least one write landed.
        deadline = time.time() + 5.0
        while time.time() < deadline:
            if read_process_identity(proc.pid) is not None and marker.exists():
                break
            time.sleep(0.05)
        self.assertIsNotNone(read_process_identity(proc.pid))
        self.assertTrue(marker.exists())
        return proc

    def _expire_active_lease(self, resource: str, *, now: str) -> None:
        row = self.store.get_active_lease(resource)
        self.assertIsNotNone(row)
        assert row is not None
        past = "2000-01-01T00:00:00Z"
        with self.store.transaction() as conn:
            conn.execute(
                "UPDATE leases SET expires_at=? WHERE lease_id=?",
                (past, row["lease_id"]),
            )
        # now is after past
        self.assertLess(past, now)

    def _marker_stub(self, spawn_marker: Path) -> Path:
        script = self.bin / "route-spawn-marker"
        return _write_exec(
            script,
            textwrap.dedent(
                f"""\
                #!/usr/bin/env bash
                set -euo pipefail
                for a in "$@"; do
                  if [[ "$a" == "--dry-run" ]]; then echo '{ROUTE_DRY}'; exit 0; fi
                done
                echo spawned > "{spawn_marker}"
                sleep 30
                """
            ),
        )

    def test_schema_v5(self) -> None:
        self.assertEqual(SCHEMA_VERSION, 5)

    def test_controller_crash_live_child_blocks_takeover(self) -> None:
        """A lease + live orphan child + expired TTL ⇒ B acquire denied; B not spawned."""
        run = self._run()
        resource = worktree_resource_key(self.worktree)
        writer_log = self.worktree / "sole-writer.log"
        child = self._spawn_orphan_writer(writer_log)
        identity = read_process_identity(child.pid)
        assert identity is not None

        now = "2026-09-15T12:00:00Z"
        exp = "2026-09-15T12:00:30Z"
        a = self.rt.start_attempt(run.run_id, worker_type="codex")
        with self.store.transaction() as conn:
            token = self.store.acquire_execution_lease(
                resource_key=resource,
                attempt_id=a.attempt_id,
                run_id=run.run_id,
                node=a.node,
                now=now,
                expires_at=exp,
                lease_id="lease_a_crash",
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
        # Simulate controller death: leave lease held (no release/reap).
        later = "2026-09-15T12:01:00Z"
        self._expire_active_lease(resource, now=later)

        with self.assertRaises(PreviousWorkerStillAliveError) as cm:
            with self.store.transaction() as conn:
                self.store.acquire_execution_lease(
                    resource_key=resource,
                    attempt_id="att_B",
                    run_id=run.run_id,
                    node=a.node,
                    now=later,
                    expires_at="2026-09-15T13:00:00Z",
                    lease_id="lease_b_crash",
                    conn=conn,
                )
        self.assertEqual(cm.exception.blocker, "previous_worker_still_alive")

        # Harness path: B must not spawn a second mutating worker.
        spawn_marker = self.root / "b-spawned.marker"
        adapter_b = RealCodexWorkerAdapter(
            codex_route=str(self._marker_stub(spawn_marker)),
            timeout_sec=2,
            canonical_db_path=self.db,
        )
        out = self.harness.step(run.run_id, worker=adapter_b, lease_ttl_sec=30)
        self.assertFalse(out.apply.accepted)
        self.assertEqual(out.apply.blocker, "previous_worker_still_alive")
        self.assertFalse(spawn_marker.exists())

        # A child remains the sole filesystem writer under the worktree log.
        before = writer_log.read_text(encoding="utf-8")
        time.sleep(0.4)
        after = writer_log.read_text(encoding="utf-8")
        self.assertGreater(len(after), len(before))
        self.assertTrue(Path(f"/proc/{child.pid}").exists())

    def test_dead_owner_reclaim_increases_fencing(self) -> None:
        run = self._run()
        resource = worktree_resource_key(self.worktree)
        writer_log = self.worktree / "dead-writer.log"
        child = self._spawn_orphan_writer(writer_log)
        identity = read_process_identity(child.pid)
        assert identity is not None

        now = "2026-09-15T12:00:00Z"
        a = self.rt.start_attempt(run.run_id, worker_type="codex")
        with self.store.transaction() as conn:
            t1 = self.store.acquire_execution_lease(
                resource_key=resource,
                attempt_id=a.attempt_id,
                run_id=run.run_id,
                node=a.node,
                now=now,
                expires_at="2026-09-15T12:00:30Z",
                lease_id="lease_a_dead",
                conn=conn,
            )
            a.fencing_token = t1
            self.store.update_attempt(a, conn=conn)
            self.store.bind_execution_identity(
                resource_key=resource,
                attempt_id=a.attempt_id,
                fencing_token=t1,
                identity=identity,
                conn=conn,
            )

        os.kill(child.pid, signal.SIGKILL)
        child.wait(timeout=5)
        self._child_pgids = [p for p in self._child_pgids if p != child.pid]
        deadline = time.time() + 5.0
        while time.time() < deadline and Path(f"/proc/{child.pid}").exists():
            time.sleep(0.05)

        later = "2026-09-15T12:01:00Z"
        self._expire_active_lease(resource, now=later)
        with self.store.transaction() as conn:
            t2 = self.store.acquire_execution_lease(
                resource_key=resource,
                attempt_id="att_B",
                run_id=run.run_id,
                node=a.node,
                now=later,
                expires_at="2026-09-15T13:00:00Z",
                lease_id="lease_b_dead",
                conn=conn,
            )
        self.assertGreater(t2, t1)
        orphaned = self.store.get_attempt(a.attempt_id)
        assert orphaned is not None
        self.assertEqual(orphaned.status, "orphaned")

    def test_unknown_pending_identity_fail_closed(self) -> None:
        """Spawn crash window: lease held, identity still pending → no takeover."""
        run = self._run()
        resource = worktree_resource_key(self.worktree)
        now = "2026-09-15T12:00:00Z"
        a = self.rt.start_attempt(run.run_id, worker_type="codex")
        with self.store.transaction() as conn:
            self.store.acquire_execution_lease(
                resource_key=resource,
                attempt_id=a.attempt_id,
                run_id=run.run_id,
                node=a.node,
                now=now,
                expires_at="2026-09-15T12:00:30Z",
                lease_id="lease_pending",
                conn=conn,
            )
        lease = self.store.get_active_lease(resource)
        assert lease is not None
        self.assertEqual(lease["identity_status"], "pending")

        later = "2026-09-15T12:01:00Z"
        self._expire_active_lease(resource, now=later)
        with self.assertRaises(PreviousWorkerUnverifiableError) as cm:
            with self.store.transaction() as conn:
                self.store.acquire_execution_lease(
                    resource_key=resource,
                    attempt_id="att_B",
                    run_id=run.run_id,
                    node=a.node,
                    now=later,
                    expires_at="2026-09-15T13:00:00Z",
                    lease_id="lease_b_pending",
                    conn=conn,
                )
        self.assertEqual(cm.exception.blocker, "previous_worker_unverifiable")

    def test_incomplete_identity_fail_closed(self) -> None:
        run = self._run()
        resource = worktree_resource_key(self.worktree)
        now = "2026-09-15T12:00:00Z"
        a = self.rt.start_attempt(run.run_id, worker_type="codex")
        with self.store.transaction() as conn:
            token = self.store.acquire_execution_lease(
                resource_key=resource,
                attempt_id=a.attempt_id,
                run_id=run.run_id,
                node=a.node,
                now=now,
                expires_at="2026-09-15T12:00:30Z",
                lease_id="lease_incomplete",
                conn=conn,
            )
            # PID alone (no starttime/boot) must not authorize reclaim.
            conn.execute(
                """
                UPDATE leases SET worker_pid=?, identity_status='bound',
                  worker_starttime_ticks=NULL, worker_boot_id=NULL
                WHERE owner=? AND fencing_token=?
                """,
                (os.getpid(), a.attempt_id, token),
            )
        later = "2026-09-15T12:01:00Z"
        self._expire_active_lease(resource, now=later)
        with self.assertRaises(PreviousWorkerUnverifiableError):
            with self.store.transaction() as conn:
                self.store.acquire_execution_lease(
                    resource_key=resource,
                    attempt_id="att_B",
                    run_id=run.run_id,
                    node=a.node,
                    now=later,
                    expires_at="2026-09-15T13:00:00Z",
                    lease_id="lease_b_incomplete",
                    conn=conn,
                )

    def test_late_result_after_dead_reclaim_fail_closed(self) -> None:
        run = self._run()
        resource = worktree_resource_key(self.worktree)
        writer_log = self.worktree / "late-writer.log"
        child = self._spawn_orphan_writer(writer_log)
        identity = read_process_identity(child.pid)
        assert identity is not None

        now = "2026-09-15T12:00:00Z"
        a = self.rt.start_attempt(run.run_id, worker_type="codex")
        with self.store.transaction() as conn:
            t1 = self.store.acquire_execution_lease(
                resource_key=resource,
                attempt_id=a.attempt_id,
                run_id=run.run_id,
                node=a.node,
                now=now,
                expires_at="2026-09-15T12:00:30Z",
                lease_id="lease_a_late",
                conn=conn,
            )
            a.fencing_token = t1
            self.store.update_attempt(a, conn=conn)
            self.store.bind_execution_identity(
                resource_key=resource,
                attempt_id=a.attempt_id,
                fencing_token=t1,
                identity=identity,
                conn=conn,
            )

        os.kill(child.pid, signal.SIGKILL)
        child.wait(timeout=5)
        self._child_pgids = [p for p in self._child_pgids if p != child.pid]

        later = "2026-09-15T12:01:00Z"
        self._expire_active_lease(resource, now=later)
        with self.store.transaction() as conn:
            t2 = self.store.acquire_execution_lease(
                resource_key=resource,
                attempt_id="att_B",
                run_id=run.run_id,
                node=a.node,
                now=later,
                expires_at="2026-09-15T13:00:00Z",
                lease_id="lease_b_late",
                conn=conn,
            )
        self.assertGreater(t2, t1)

        late = self.store.get_attempt(a.attempt_id)
        assert late is not None
        self.assertEqual(late.status, "orphaned")
        payload = {
            "schema_version": "1.0",
            "status": "success",
            "summary": "late-from-A",
            "idempotency_key": f"{late.attempt_id}:INVESTIGATION_COMPLETED",
            "artifacts": [],
            "evidence": [{"kind": "t", "ref": "late"}],
            "proposed_outcome": {
                "outcome_type": "INVESTIGATION_COMPLETED",
                "actor_id": "late",
                "actor_role": "investigator",
                "head_sha": self.base_sha,
                "base_sha": self.base_sha,
                "conclusion": "ok",
                "evidence": {},
                "repository": "jerry200176-png/portfolio-ops",
            },
        }
        out = self.harness.ingest_worker_result(
            run_id=run.run_id, attempt_id=late.attempt_id, result=payload
        )
        self.assertFalse(out.apply.accepted)
        self.assertEqual(out.apply.blocker, "stale_execution_lease")
        self.assertEqual(self.rt.get_run(run.run_id).current_node, "investigator")
        self.assertEqual(self.rt.get_run(run.run_id).state_version, 1)


if __name__ == "__main__":
    unittest.main()
