"""Tests for Part A dogfood evidence assembler."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_graph.dogfood_evidence import collect_dogfood_evidence
from agent_graph.durable_runtime import DurableGraphRuntime
from agent_graph.harness import FakeWorkerAdapter, GraphHarness
from agent_graph.sqlite_store import SqliteControlPlaneStore


class DogfoodEvidenceTests(unittest.TestCase):
    def test_collect_includes_required_keys(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        db = Path(tmp.name) / "g.sqlite"
        store = SqliteControlPlaneStore(str(db))
        rt = DurableGraphRuntime(store)
        harness = GraphHarness(rt)
        head = "b" * 40
        base = "a" * 40
        run = rt.create_run(objective="ev", project="portfolio-ops", base_sha=base)
        w = FakeWorkerAdapter(head_sha=head)
        harness.step(run.run_id, worker=w, write_context=False)
        ev = collect_dogfood_evidence(
            runtime=rt, store=store, run_id=run.run_id, scheduler_id="sched_test"
        )
        for key in (
            "run_id",
            "attempt_ids",
            "worker_identities",
            "node_transitions",
            "changed_files",
            "test_evidence",
            "pr",
            "exact_head_sha",
            "ci_state",
            "approvals",
            "effect_ids",
            "merge_sha",
            "terminal_reconciliation",
        ):
            self.assertIn(key, ev)
        self.assertEqual(ev["run_id"], run.run_id)
        self.assertTrue(ev["attempt_ids"])
        rt.close()


if __name__ == "__main__":
    unittest.main()
