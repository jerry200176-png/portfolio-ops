"""Phase 1A durable Graph Control Plane tests (stdlib unittest)."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from agent_graph.durable_runtime import DurableGraphRuntime
from agent_graph.harness import FakeWorkerAdapter, GraphHarness, write_worker_context
from agent_graph.models import Event
from agent_graph.sqlite_store import SCHEMA_VERSION, SqliteControlPlaneStore
from agent_graph.worker_contract import WorkerResultError, validate_worker_result, write_worker_result


class DurableControlPlaneTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / "graph-control.sqlite"
        self.store = SqliteControlPlaneStore(self.db_path)
        self.rt = DurableGraphRuntime(self.store)
        self.harness = GraphHarness(self.rt)

    def tearDown(self) -> None:
        self.rt.close()
        self.tmp.cleanup()

    def test_schema_migration_init_and_wal(self) -> None:
        self.assertEqual(self.store.pragma_journal_mode(), "wal")
        row = self.store._conn.execute(
            "SELECT version FROM schema_migrations ORDER BY version DESC LIMIT 1"
        ).fetchone()
        self.assertEqual(int(row["version"]), SCHEMA_VERSION)
        # reopen migrates idempotently
        self.rt.close()
        store2 = SqliteControlPlaneStore(self.db_path)
        self.assertEqual(store2.pragma_journal_mode(), "wal")
        store2.close()
        # recreate runtime for tearDown
        self.store = SqliteControlPlaneStore(self.db_path)
        self.rt = DurableGraphRuntime(self.store)
        self.harness = GraphHarness(self.rt)

    def test_run_creation(self) -> None:
        run = self.rt.create_run(
            objective="demo durable slice",
            project="portfolio-ops",
            base_sha="a" * 40,
        )
        self.assertEqual(run.current_node, "investigator")
        self.assertEqual(run.status, "running")
        self.assertEqual(run.graph_version, "v0")
        events = self.rt.list_events(run.run_id)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].type, "TASK_CREATED")

    def test_valid_transition_via_step(self) -> None:
        run = self.rt.create_run(objective="x", project="portfolio-ops", base_sha="a" * 40)
        out = self.harness.step(run.run_id, worker=FakeWorkerAdapter(head_sha="b" * 40), write_context=False)
        self.assertTrue(out.apply.accepted)
        self.assertEqual(out.apply.run.current_node, "builder")

    def test_invalid_transition_fail_closed(self) -> None:
        run = self.rt.create_run(objective="x", project="portfolio-ops", base_sha="a" * 40)
        # Skip investigator: try BUILD_COMPLETED directly
        bad = Event(
            event_id="bad-build",
            task_id=run.run_id,
            timestamp="2026-09-15T00:00:00Z",
            event_type="BUILD_COMPLETED",
            node="builder",
            actor_id="builder-1",
            actor_role="builder",
            repository="jerry200176-png/portfolio-ops",
            base_sha="a" * 40,
            head_sha="b" * 40,
            conclusion="ok",
            evidence={},
        )
        result = self.rt.apply_graph_event(run_id=run.run_id, event=bad, expected_state_version=1)
        self.assertFalse(result.accepted)
        self.assertIn("illegal transition", result.reason or "")
        self.assertEqual(len(self.rt.list_events(run.run_id)), 1)

    def test_atomic_event_and_projection(self) -> None:
        run = self.rt.create_run(objective="x", project="portfolio-ops", base_sha="a" * 40)
        before = self.rt.get_run(run.run_id)
        self.harness.step(run.run_id, worker=FakeWorkerAdapter(), write_context=False)
        after = self.rt.get_run(run.run_id)
        self.assertNotEqual(before.current_node, after.current_node)
        self.assertEqual(after.graph_snapshot["current_node"], after.current_node)
        # event count matches progression
        self.assertEqual(len(self.rt.list_events(run.run_id)), 2)

    def test_duplicate_event_idempotent(self) -> None:
        run = self.rt.create_run(objective="x", project="portfolio-ops", base_sha="a" * 40)
        event = Event(
            event_id=f"{run.run_id}:TASK_CREATED",
            task_id=run.run_id,
            timestamp=run.created_at,
            event_type="TASK_CREATED",
            node="intake",
            actor_id="system",
            actor_role="system",
            repository="jerry200176-png/portfolio-ops",
            base_sha="a" * 40,
            head_sha="a" * 40,
            conclusion="created",
            evidence={"objective": "x"},
        )
        # Rebuild exact payload from stored event for true idempotency
        stored = self.rt.list_events(run.run_id)[0]
        event = Event.from_dict(stored.payload)
        r = self.rt.apply_graph_event(
            run_id=run.run_id, event=event, expected_state_version=run.state_version
        )
        self.assertTrue(r.accepted)
        self.assertTrue(r.duplicate)
        self.assertEqual(len(self.rt.list_events(run.run_id)), 1)

    def test_duplicate_result_ingest_idempotent(self) -> None:
        run = self.rt.create_run(objective="x", project="portfolio-ops", base_sha="a" * 40)
        first = self.harness.step(run.run_id, worker=FakeWorkerAdapter(), write_context=False)
        self.assertTrue(first.apply.accepted)
        # Re-ingest same result payload against same attempt
        from agent_graph.worker_contract import validate_worker_result

        # Reconstruct result with same idempotency key
        result = {
            "schema_version": "1.0",
            "status": "success",
            "summary": "retry",
            "idempotency_key": first.attempt.result_ingest_key,
            "artifacts": [{"kind": "note", "uri": "fake://x"}],
            "evidence": [{"kind": "fixture", "ref": first.attempt.attempt_id}],
            "proposed_outcome": {
                "outcome_type": "INVESTIGATION_COMPLETED",
                "actor_id": "inv-1",
                "actor_role": "investigator",
                "head_sha": "a" * 40,
                "base_sha": "a" * 40,
                "conclusion": "ok",
                "evidence": {"source": "fake_worker"},
                "repository": "jerry200176-png/portfolio-ops",
            },
        }
        validate_worker_result(result)
        second = self.harness.ingest_worker_result(
            run_id=run.run_id,
            attempt_id=first.attempt.attempt_id,
            result=result,
        )
        self.assertTrue(second.duplicate_ingest)
        self.assertEqual(len(self.rt.list_events(run.run_id)), 2)

    def test_attempt_lifecycle(self) -> None:
        run = self.rt.create_run(objective="x", project="portfolio-ops", base_sha="a" * 40)
        att = self.rt.start_attempt(run.run_id, worker_type="fake", worker_pid=12345)
        self.assertEqual(att.status, "started")
        self.assertEqual(att.node, "investigator")
        self.assertEqual(att.worker_pid, 12345)
        loaded = self.rt.store.get_attempt(att.attempt_id)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.status, "started")

    def test_structured_result_validation_rejects_next_node(self) -> None:
        with self.assertRaises(WorkerResultError):
            validate_worker_result(
                {
                    "status": "success",
                    "summary": "bad",
                    "idempotency_key": "k1",
                    "artifacts": [],
                    "evidence": [],
                    "next_node": "builder",
                    "proposed_outcome": {
                        "outcome_type": "INVESTIGATION_COMPLETED",
                        "actor_id": "inv-1",
                        "actor_role": "investigator",
                    },
                }
            )

    def test_worker_cannot_determine_arbitrary_next_node(self) -> None:
        run = self.rt.create_run(objective="x", project="portfolio-ops", base_sha="a" * 40)
        att = self.rt.start_attempt(run.run_id, worker_type="fake")
        # Worker proposes BUILD_COMPLETED while on investigator — rejected by harness
        bad = {
            "schema_version": "1.0",
            "status": "success",
            "summary": "smuggle",
            "idempotency_key": f"{att.attempt_id}:smuggle",
            "artifacts": [],
            "evidence": [{"kind": "x", "ref": "y"}],
            "proposed_outcome": {
                "outcome_type": "BUILD_COMPLETED",
                "actor_id": "builder-1",
                "actor_role": "builder",
                "head_sha": "b" * 40,
            },
        }
        with self.assertRaises(WorkerResultError):
            self.harness.ingest_worker_result(
                run_id=run.run_id, attempt_id=att.attempt_id, result=bad
            )
        self.assertEqual(self.rt.get_run(run.run_id).current_node, "investigator")

    def test_crash_reload_resume(self) -> None:
        run = self.rt.create_run(
            objective="crash-resume proof",
            project="portfolio-ops",
            base_sha="a" * 40,
        )
        run_id = run.run_id
        step1 = self.harness.step(
            run_id, worker=FakeWorkerAdapter(head_sha="b" * 40), write_context=False
        )
        self.assertTrue(step1.apply.accepted)
        self.assertEqual(step1.apply.run.current_node, "builder")
        events_before = [e.to_dict() for e in self.rt.list_events(run_id)]

        # Process/runtime fully ends.
        self.rt.close()
        self.rt = None
        self.store = None
        self.harness = None

        # Brand-new process context.
        store2 = SqliteControlPlaneStore(self.db_path)
        rt2 = DurableGraphRuntime(store2)
        harness2 = GraphHarness(rt2)
        reloaded = rt2.get_run(run_id)
        self.assertEqual(reloaded.current_node, "builder")
        self.assertEqual(reloaded.status, "running")
        events_after = [e.to_dict() for e in rt2.list_events(run_id)]
        self.assertEqual(events_after, events_before)

        step2 = harness2.step(
            run_id, worker=FakeWorkerAdapter(head_sha="b" * 40), write_context=False
        )
        self.assertTrue(step2.apply.accepted)
        self.assertEqual(step2.apply.run.current_node, "reviewer")
        # No Codex conversation involved.
        self.assertIsNone(reloaded.graph_snapshot.get("codex_thread_id", None))

        rt2.close()
        # restore for tearDown
        self.store = SqliteControlPlaneStore(self.db_path)
        self.rt = DurableGraphRuntime(self.store)
        self.harness = GraphHarness(self.rt)

    def test_full_fixture_path_to_human_gate_and_approve(self) -> None:
        run = self.rt.create_run(objective="full", project="portfolio-ops", base_sha="a" * 40)
        head = "b" * 40
        worker = FakeWorkerAdapter(head_sha=head)
        for expected in ("builder", "reviewer", "human_gate"):
            out = self.harness.step(run.run_id, worker=worker, write_context=False)
            self.assertTrue(out.apply.accepted, out.apply.reason)
            self.assertEqual(out.apply.run.current_node, expected)
        waiting = self.rt.get_run(run.run_id)
        self.assertEqual(waiting.status, "waiting_for_approval")
        self.assertEqual(waiting.current_node, "human_gate")
        approved = self.rt.grant_founder_approval(
            run_id=run.run_id,
            action="approve_effect",
            head_sha=head,
            actor="founder",
        )
        self.assertTrue(approved["accepted"], approved)
        final = self.rt.get_run(run.run_id)
        self.assertEqual(final.status, "approved_for_effect")
        self.assertEqual(final.current_node, "approved_for_effect")
        self.assertTrue(final.human_approved)
        self.assertFalse(final.closed)

    def test_worker_context_and_result_file_handoff(self) -> None:
        wt = Path(self.tmp.name) / "wt"
        (wt / ".agent-session").mkdir(parents=True)
        (wt / ".agent-session" / "manifest.json").write_text(
            json.dumps(
                {
                    "schema_version": "1.0",
                    "session_id": "abcd1234",
                    "project": "portfolio-ops",
                    "task_id": "t1",
                    "repo_remote": "https://example.invalid/r.git",
                    "base_sha": "a" * 40,
                    "branch": "chore/task-t1",
                    "worktree_path": str(wt),
                    "started_at": "2026-09-15T00:00:00Z",
                    "production_mutation": False,
                    "preflight_result": "pass",
                    "provenance_type": "agent-session",
                }
            ),
            encoding="utf-8",
        )
        run = self.rt.create_run(
            objective="ctx",
            project="portfolio-ops",
            base_sha="a" * 40,
            worktree=str(wt),
            branch="chore/task-t1",
        )
        out = self.harness.step(run.run_id, worker=FakeWorkerAdapter(), write_context=True)
        self.assertTrue(out.apply.accepted)
        binding = json.loads((wt / ".agent-session" / "graph-binding.json").read_text())
        self.assertEqual(binding["run_id"], run.run_id)
        self.assertEqual(binding["node"], "investigator")
        self.assertIn("expected_state_version", binding)
        # Manifest is not the graph binding contract; do not require run_id fields there.
        self.assertTrue((wt / ".agent-session" / "result.json").is_file())
        self.assertTrue((wt / ".agent-session" / "worker-context.json").is_file())
        ctx = json.loads((wt / ".agent-session" / "worker-context.json").read_text())
        self.assertEqual(ctx["EXPECTED_STATE_VERSION"], binding["expected_state_version"])

    def test_write_worker_result_roundtrip(self) -> None:
        path = Path(self.tmp.name) / "result.json"
        payload = {
            "schema_version": "1.0",
            "status": "success",
            "summary": "ok",
            "idempotency_key": "k",
            "artifacts": [{"kind": "log", "uri": "file://x"}],
            "evidence": [{"kind": "test", "ref": "1"}],
            "proposed_outcome": {
                "outcome_type": "INVESTIGATION_COMPLETED",
                "actor_id": "inv-1",
                "actor_role": "investigator",
            },
        }
        write_worker_result(path, payload)
        from agent_graph.worker_contract import read_worker_result

        loaded = read_worker_result(path)
        self.assertEqual(loaded.idempotency_key, "k")


if __name__ == "__main__":
    unittest.main()
