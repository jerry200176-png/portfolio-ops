"""Phase 1B harden: path boundary, identity, lease, process lifecycle."""

from __future__ import annotations

import json
import os
import stat
import tempfile
import textwrap
import time
import unittest
from pathlib import Path

from agent_graph.canonical_paths import (
    CanonicalPathError,
    assert_canonical_db_outside_worktree,
    safe_result_path,
    worktree_resource_key,
)
from agent_graph.durable_runtime import DurableGraphRuntime
from agent_graph.harness import GraphHarness
from agent_graph.real_codex_adapter import RealCodexWorkerAdapter
from agent_graph.sqlite_store import LeaseBusyError, SCHEMA_VERSION, SqliteControlPlaneStore, StaleLeaseError
from agent_graph.worker_contract import RESULT_REL_PATH, WorkerResultError, write_worker_result


def _write_exec(path: Path, body: str) -> Path:
    path.write_text(body, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IEXEC)
    return path


ROUTE_DRY = (
    '{"profile":"terra","model":"stub","reasoning_effort_override":null,'
    '"reason":"t","resolution":"selected","requested_tier":"terra","selected_tier":"terra"}'
)


class Phase1BHardenTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        # Canonical DB OUTSIDE the worker worktree (capability boundary).
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

    def tearDown(self) -> None:
        self.rt.close()
        self.tmp.cleanup()

    def _run(self):
        return self.rt.create_run(
            objective="harden",
            project="portfolio-ops",
            base_sha=self.base_sha,
            worktree=str(self.worktree),
            branch="t",
        )

    def _success_stub(self) -> Path:
        script = self.bin / "route-ok"
        return _write_exec(
            script,
            textwrap.dedent(
                f"""\
                #!/usr/bin/env bash
                set -euo pipefail
                for a in "$@"; do
                  if [[ "$a" == "--dry-run" ]]; then echo '{ROUTE_DRY}'; exit 0; fi
                done
                wt=""; prev=""
                for arg in "$@"; do
                  if [[ "$prev" == "-C" ]]; then wt="$arg"; fi
                  prev="$arg"
                done
                mkdir -p "$wt/.agent-session"
                attempt="${{ATTEMPT_ID:?}}"
                cat > "$wt/{RESULT_REL_PATH}" <<EOF
                {{
                  "schema_version": "1.0",
                  "status": "success",
                  "summary": "ok",
                  "idempotency_key": "${{attempt}}:INVESTIGATION_COMPLETED",
                  "artifacts": [],
                  "evidence": [{{"kind": "t", "ref": "${{attempt}}"}}],
                  "proposed_outcome": {{
                    "outcome_type": "INVESTIGATION_COMPLETED",
                    "actor_id": "stub-${{attempt}}",
                    "actor_role": "investigator",
                    "head_sha": "{self.base_sha}",
                    "base_sha": "{self.base_sha}",
                    "conclusion": "ok",
                    "evidence": {{}},
                    "repository": "jerry200176-png/portfolio-ops"
                  }}
                }}
                EOF
                """
            ),
        )

    def test_schema_version_is_v6(self) -> None:
        self.assertEqual(SCHEMA_VERSION, 6)

    def test_canonical_db_inside_worktree_refused(self) -> None:
        bad_db = self.worktree / "state" / "graph.sqlite"
        bad_db.parent.mkdir(parents=True)
        with self.assertRaises(CanonicalPathError):
            assert_canonical_db_outside_worktree(bad_db, self.worktree)
        adapter = RealCodexWorkerAdapter(
            codex_route=str(self._success_stub()),
            canonical_db_path=bad_db,
            timeout_sec=5,
        )
        run = self._run()
        with self.assertRaises(Exception):
            self.harness.step(
                run.run_id,
                worker=adapter,
                extra_context={"CANONICAL_DB_PATH": str(bad_db)},
            )

    def test_direct_canonical_store_mutation_impossible_from_worktree_scope(self) -> None:
        """Worker writable scope is the worktree; canonical DB is outside it.

        Capability proof without Codex: open/create under worktree cannot reach DB.
        """
        assert_canonical_db_outside_worktree(self.db, self.worktree)
        before = self.db.read_bytes()
        # Simulate sandbox: only paths under worktree are writable.
        target = self.worktree / "state" / "graph-control.sqlite"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("attacker", encoding="utf-8")
        self.assertEqual(self.db.read_bytes(), before)
        # Canonical Run unchanged.
        run = self._run()
        ver = self.rt.get_run(run.run_id).state_version
        self.assertEqual(ver, 1)
        self.assertFalse(any(self.worktree.resolve() in p.parents or p == self.worktree.resolve()
                             for p in [self.db.resolve()]))

    def test_identity_tamper_in_result_fail_closed(self) -> None:
        run = self._run()
        attempt = self.rt.start_attempt(run.run_id, worker_type="fake")
        bad = {
            "schema_version": "1.0",
            "status": "success",
            "summary": "tamper",
            "idempotency_key": f"{attempt.attempt_id}:INVESTIGATION_COMPLETED",
            "run_id": "run_OTHER",
            "artifacts": [],
            "evidence": [{"kind": "t", "ref": "x"}],
            "proposed_outcome": {
                "outcome_type": "INVESTIGATION_COMPLETED",
                "actor_id": "x",
                "actor_role": "investigator",
                "head_sha": self.base_sha,
                "base_sha": self.base_sha,
                "conclusion": "ok",
                "evidence": {},
                "repository": "jerry200176-png/portfolio-ops",
            },
        }
        with self.assertRaises(WorkerResultError):
            self.harness.ingest_worker_result(
                run_id=run.run_id, attempt_id=attempt.attempt_id, result=bad
            )
        self.assertEqual(self.rt.get_run(run.run_id).current_node, "investigator")

    def test_binding_file_tamper_ignored_controller_attempt_wins(self) -> None:
        run = self._run()
        route = self._success_stub()
        adapter = RealCodexWorkerAdapter(
            codex_route=str(route),
            timeout_sec=10,
            canonical_db_path=self.db,
        )
        # Pre-write tampered binding; controller still uses SQLite Attempt.
        session = self.worktree / ".agent-session"
        session.mkdir(parents=True, exist_ok=True)
        (session / "graph-binding.json").write_text(
            json.dumps(
                {
                    "run_id": "run_FORGED",
                    "attempt_id": "att_FORGED",
                    "node": "builder",
                    "expected_state_version": 999,
                }
            ),
            encoding="utf-8",
        )
        out = self.harness.step(run.run_id, worker=adapter)
        self.assertTrue(out.apply.accepted)
        self.assertEqual(out.apply.run.current_node, "builder")
        self.assertNotEqual(out.attempt.attempt_id, "att_FORGED")

    def test_result_symlink_escape_rejected(self) -> None:
        run = self._run()
        session = self.worktree / ".agent-session"
        session.mkdir(parents=True, exist_ok=True)
        outside = self.root / "secret-control.json"
        outside.write_text('{"status":"success"}', encoding="utf-8")
        link = session / "result.json"
        link.symlink_to(outside)
        with self.assertRaises(CanonicalPathError):
            safe_result_path(self.worktree)

    def test_execution_lease_mutual_exclusion_and_reacquire(self) -> None:
        run = self._run()
        now = "2026-09-15T00:00:00Z"
        exp = "2026-09-15T01:00:00Z"
        resource = worktree_resource_key(self.worktree)
        with self.store.transaction() as conn:
            t1 = self.store.acquire_execution_lease(
                resource_key=resource,
                attempt_id="att_A",
                run_id=run.run_id,
                node="investigator",
                now=now,
                expires_at=exp,
                lease_id="lease_a",
                conn=conn,
            )
        self.assertEqual(t1, 1)
        with self.assertRaises(LeaseBusyError):
            with self.store.transaction() as conn:
                self.store.acquire_execution_lease(
                    resource_key=resource,
                    attempt_id="att_B",
                    run_id=run.run_id,
                    node="investigator",
                    now=now,
                    expires_at=exp,
                    lease_id="lease_b",
                    conn=conn,
                )
        with self.store.transaction() as conn:
            self.assertTrue(
                self.store.release_execution_lease(
                    resource_key=resource,
                    attempt_id="att_A",
                    fencing_token=t1,
                    now=now,
                    conn=conn,
                )
            )
            t2 = self.store.acquire_execution_lease(
                resource_key=resource,
                attempt_id="att_B",
                run_id=run.run_id,
                node="investigator",
                now=now,
                expires_at=exp,
                lease_id="lease_b2",
                conn=conn,
            )
        self.assertEqual(t2, 2)

    def test_stale_fencing_token_fail_closed(self) -> None:
        run = self._run()
        now = "2026-09-15T00:00:00Z"
        exp = "2026-09-15T01:00:00Z"
        resource = worktree_resource_key(self.worktree)
        with self.store.transaction() as conn:
            t1 = self.store.acquire_execution_lease(
                resource_key=resource,
                attempt_id="att_A",
                run_id=run.run_id,
                node="investigator",
                now=now,
                expires_at=exp,
                lease_id="lease_a",
                conn=conn,
            )
            self.store.release_execution_lease(
                resource_key=resource,
                attempt_id="att_A",
                fencing_token=t1,
                now=now,
                conn=conn,
            )
            t2 = self.store.acquire_execution_lease(
                resource_key=resource,
                attempt_id="att_B",
                run_id=run.run_id,
                node="investigator",
                now=now,
                expires_at=exp,
                lease_id="lease_b",
                conn=conn,
            )
        self.assertGreater(t2, t1)
        with self.assertRaises(StaleLeaseError):
            self.store.assert_lease_fence(
                resource_key=resource,
                attempt_id="att_A",
                fencing_token=t1,
                now=now,
            )

    def test_late_result_after_lease_generation_change_fail_closed(self) -> None:
        run = self._run()
        a = self.rt.start_attempt(run.run_id, worker_type="codex")
        now = "2026-09-15T00:00:00Z"
        exp = "2026-09-15T01:00:00Z"
        resource = worktree_resource_key(self.worktree)
        with self.store.transaction() as conn:
            token = self.store.acquire_execution_lease(
                resource_key=resource,
                attempt_id=a.attempt_id,
                run_id=run.run_id,
                node=a.node,
                now=now,
                expires_at=exp,
                lease_id="lease_a",
                conn=conn,
            )
            a.fencing_token = token
            self.store.update_attempt(a, conn=conn)
            self.store.release_execution_lease(
                resource_key=resource,
                attempt_id=a.attempt_id,
                fencing_token=token,
                now=now,
                conn=conn,
            )
            self.store.acquire_execution_lease(
                resource_key=resource,
                attempt_id="att_B",
                run_id=run.run_id,
                node=a.node,
                now=now,
                expires_at=exp,
                lease_id="lease_b",
                conn=conn,
            )
        # Reload attempt with old fencing token; late success must fail closed.
        late = self.store.get_attempt(a.attempt_id)
        assert late is not None
        payload = {
            "schema_version": "1.0",
            "status": "success",
            "summary": "late",
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

    def test_process_group_timeout_reaps_children(self) -> None:
        stub = self.bin / "route-tree"
        _write_exec(
            stub,
            textwrap.dedent(
                f"""\
                #!/usr/bin/env bash
                set -euo pipefail
                for a in "$@"; do
                  if [[ "$a" == "--dry-run" ]]; then echo '{ROUTE_DRY}'; exit 0; fi
                done
                # Child that would otherwise outlive a plain kill of the parent.
                sleep 60 &
                sleep 60
                """
            ),
        )
        run = self._run()
        adapter = RealCodexWorkerAdapter(
            codex_route=str(stub),
            timeout_sec=0.4,
            terminate_grace_sec=1.0,
            canonical_db_path=self.db,
        )
        out = self.harness.step(run.run_id, worker=adapter)
        self.assertFalse(out.apply.accepted)
        self.assertTrue(adapter.last_launch.timed_out)
        pid = adapter.last_launch.pid
        self.assertIsNotNone(pid)
        time.sleep(0.2)
        try:
            os.kill(pid, 0)
            alive = True
        except ProcessLookupError:
            alive = False
        self.assertFalse(alive)
        self.assertEqual(self.rt.get_run(run.run_id).current_node, "investigator")


if __name__ == "__main__":
    unittest.main()
