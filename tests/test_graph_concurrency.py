"""Concurrency, contention, and event-replay invariants for Phase 1A."""

from __future__ import annotations

import multiprocessing as mp
import sqlite3
import sys
import tempfile
import time
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from agent_graph.durable_runtime import DurableGraphRuntime
from agent_graph.harness import FakeWorkerAdapter, GraphHarness
from agent_graph.models import Event
from agent_graph.sqlite_store import DEFAULT_BUSY_TIMEOUT_MS, SCHEMA_VERSION, SqliteControlPlaneStore


def _utcnow() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _investigation_event(run_id: str, event_id: str, base_sha: str) -> Event:
    return Event(
        event_id=event_id,
        task_id=run_id,
        timestamp=_utcnow(),
        event_type="INVESTIGATION_COMPLETED",
        node="investigator",
        actor_id=f"inv-{event_id[-4:]}",
        actor_role="investigator",
        repository="jerry200176-png/portfolio-ops",
        base_sha=base_sha,
        head_sha=base_sha,
        conclusion="ok",
        evidence={"source": "concurrent-test"},
    )


def _contention_worker(
    db_path: str,
    run_id: str,
    event_id: str,
    expected_version: int,
    base_sha: str,
    queue: mp.Queue,
) -> None:
    store = SqliteControlPlaneStore(db_path, busy_timeout_ms=5000)
    rt = DurableGraphRuntime(store)
    try:
        result = rt.apply_graph_event(
            run_id=run_id,
            event=_investigation_event(run_id, event_id, base_sha),
            expected_state_version=expected_version,
        )
        queue.put(
            {
                "accepted": result.accepted,
                "reason": result.reason,
                "blocker": result.blocker,
            }
        )
    finally:
        rt.close()


def _concurrent_worker(
    db_path: str,
    run_id: str,
    event_id: str,
    expected_version: int,
    base_sha: str,
    queue: mp.Queue,
) -> None:
    store = SqliteControlPlaneStore(db_path, busy_timeout_ms=5000)
    rt = DurableGraphRuntime(store)
    try:
        result = rt.apply_graph_event(
            run_id=run_id,
            event=_investigation_event(run_id, event_id, base_sha),
            expected_state_version=expected_version,
        )
        queue.put(
            {
                "accepted": result.accepted,
                "duplicate": result.duplicate,
                "reason": result.reason,
                "blocker": result.blocker,
                "version": result.run.state_version,
                "node": result.run.current_node,
                "event_id": event_id,
            }
        )
    except Exception as exc:  # pragma: no cover - surfaced to parent assertions
        queue.put({"error": f"{type(exc).__name__}: {exc}", "event_id": event_id})
    finally:
        rt.close()


class ConcurrencyReplayTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / "graph-control.sqlite"
        self.store = SqliteControlPlaneStore(self.db_path)
        self.rt = DurableGraphRuntime(self.store)
        self.harness = GraphHarness(self.rt)
        self.base_sha = "a" * 40

    def tearDown(self) -> None:
        self.rt.close()
        self.tmp.cleanup()

    def test_state_version_monotonic_on_transition(self) -> None:
        run = self.rt.create_run(
            objective="version",
            project="portfolio-ops",
            base_sha=self.base_sha,
        )
        self.assertEqual(run.state_version, 1)  # TASK_CREATED
        out = self.harness.step(
            run.run_id, worker=FakeWorkerAdapter(head_sha="b" * 40), write_context=False
        )
        self.assertTrue(out.apply.accepted)
        self.assertGreater(out.apply.run.state_version, 1)
        # start_attempt bumps once, ingest transition bumps again (+ optional tested_sha)
        self.assertGreaterEqual(out.apply.run.state_version, 3)

    def test_stale_expected_version_rejected(self) -> None:
        run = self.rt.create_run(
            objective="stale",
            project="portfolio-ops",
            base_sha=self.base_sha,
        )
        stale = self.rt.apply_graph_event(
            run_id=run.run_id,
            event=_investigation_event(run.run_id, "e-stale", self.base_sha),
            expected_state_version=0,  # actual is 1 after create
        )
        self.assertFalse(stale.accepted)
        self.assertEqual(stale.blocker, "stale_state_version")
        self.assertEqual(self.rt.get_run(run.run_id).current_node, "investigator")
        self.assertEqual(len(self.rt.list_events(run.run_id)), 1)

    def test_concurrent_mutual_exclusion_one_success(self) -> None:
        run = self.rt.create_run(
            objective="mutex",
            project="portfolio-ops",
            base_sha=self.base_sha,
        )
        run_id = run.run_id
        expected_version = run.state_version
        self.assertEqual(expected_version, 1)
        # Close parent connection before child processes open the same DB file.
        self.rt.close()

        ctx = mp.get_context("spawn")
        queue: mp.Queue = ctx.Queue()
        procs = [
            ctx.Process(
                target=_concurrent_worker,
                args=(
                    str(self.db_path),
                    run_id,
                    f"evt-a-{i}",
                    expected_version,
                    self.base_sha,
                    queue,
                ),
            )
            for i in range(2)
        ]
        for p in procs:
            p.start()
        results = [queue.get(timeout=30) for _ in procs]
        for p in procs:
            p.join(timeout=30)
            self.assertEqual(p.exitcode, 0)

        self.assertTrue(all("error" not in r for r in results), results)
        accepted = [r for r in results if r.get("accepted")]
        rejected = [r for r in results if not r.get("accepted")]
        self.assertEqual(len(accepted), 1, results)
        self.assertEqual(len(rejected), 1, results)
        # Loser is either stale version or illegal transition after winner committed.
        loser = rejected[0]
        self.assertTrue(
            loser.get("blocker") in {"stale_state_version", None}
            or "illegal transition" in (loser.get("reason") or "")
            or "stale state_version" in (loser.get("reason") or ""),
            loser,
        )

        # Reopen and verify integrity.
        store = SqliteControlPlaneStore(self.db_path)
        rt = DurableGraphRuntime(store)
        events = rt.list_events(run_id)
        # Exactly one investigation completion (plus create).
        inv = [e for e in events if e.type == "INVESTIGATION_COMPLETED"]
        self.assertEqual(len(inv), 1)
        final = rt.get_run(run_id)
        self.assertEqual(final.current_node, "builder")
        verify = rt.verify_projection_matches_events(run_id)
        self.assertTrue(verify["equal"], verify)
        rt.close()

        # Restore for tearDown
        self.store = SqliteControlPlaneStore(self.db_path)
        self.rt = DurableGraphRuntime(self.store)
        self.harness = GraphHarness(self.rt)

    def test_event_replay_matches_projection(self) -> None:
        run = self.rt.create_run(
            objective="replay",
            project="portfolio-ops",
            base_sha=self.base_sha,
        )
        worker = FakeWorkerAdapter(head_sha="b" * 40)
        for _ in range(3):
            out = self.harness.step(run.run_id, worker=worker, write_context=False)
            self.assertTrue(out.apply.accepted, out.apply.reason)

        # New process/context
        self.rt.close()
        store = SqliteControlPlaneStore(self.db_path)
        rt = DurableGraphRuntime(store)
        verify = rt.verify_projection_matches_events(run.run_id)
        self.assertTrue(verify["equal"], verify)
        rt.close()
        self.store = SqliteControlPlaneStore(self.db_path)
        self.rt = DurableGraphRuntime(self.store)
        self.harness = GraphHarness(self.rt)

    def test_busy_timeout_is_bounded(self) -> None:
        # Holder keeps an exclusive write lock longer than waiter timeout.
        holder = sqlite3.connect(str(self.db_path), isolation_level=None, timeout=0.05)
        holder.execute("PRAGMA busy_timeout = 50")
        holder.execute("BEGIN IMMEDIATE")
        holder.execute("CREATE TABLE IF NOT EXISTS lock_probe(id INTEGER PRIMARY KEY)")

        waiter = SqliteControlPlaneStore(self.db_path, busy_timeout_ms=50)
        started = time.monotonic()
        with self.assertRaises(sqlite3.OperationalError):
            with waiter.transaction():
                waiter._conn.execute("SELECT 1 FROM runs LIMIT 1")
        elapsed = time.monotonic() - started
        self.assertLess(elapsed, 2.0)
        holder.execute("COMMIT")
        holder.close()
        waiter.close()

        # Restore default store for tearDown (original still open from setUp).
        # Keep self.rt as-is.

    def test_contention_eventually_serializes_without_loss(self) -> None:
        run = self.rt.create_run(
            objective="contend",
            project="portfolio-ops",
            base_sha=self.base_sha,
        )
        run_id = run.run_id
        version = run.state_version
        self.rt.close()

        ctx = mp.get_context("spawn")
        queue: mp.Queue = ctx.Queue()
        p1 = ctx.Process(
            target=_contention_worker,
            args=(str(self.db_path), run_id, "contend-1", version, self.base_sha, queue),
        )
        p2 = ctx.Process(
            target=_contention_worker,
            args=(str(self.db_path), run_id, "contend-2", version, self.base_sha, queue),
        )
        p1.start()
        p2.start()
        outs = [queue.get(timeout=30), queue.get(timeout=30)]
        p1.join(timeout=30)
        p2.join(timeout=30)
        self.assertEqual(p1.exitcode, 0)
        self.assertEqual(p2.exitcode, 0)
        self.assertEqual(sum(1 for o in outs if o["accepted"]), 1, outs)

        store = SqliteControlPlaneStore(self.db_path)
        rt = DurableGraphRuntime(store)
        inv = [e for e in rt.list_events(run_id) if e.type == "INVESTIGATION_COMPLETED"]
        self.assertEqual(len(inv), 1)
        self.assertTrue(rt.verify_projection_matches_events(run_id)["equal"])
        rt.close()

        self.store = SqliteControlPlaneStore(self.db_path)
        self.rt = DurableGraphRuntime(self.store)
        self.harness = GraphHarness(self.rt)

    def test_schema_version_is_v2(self) -> None:
        self.assertEqual(SCHEMA_VERSION, 2)
        self.assertEqual(self.store.pragma_journal_mode(), "wal")
        self.assertGreaterEqual(DEFAULT_BUSY_TIMEOUT_MS, 1)


if __name__ == "__main__":
    unittest.main()
