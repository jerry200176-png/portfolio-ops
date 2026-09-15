"""Phase 1D+: Effect Journal, reconcile, scheduler (no production deploy)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_graph.durable_runtime import DurableGraphRuntime
from agent_graph.effect_allowlist import assert_effect_allowed
from agent_graph.github_mutate import FakeGitHubMutator, MutationError
from agent_graph.github_observe import FakeGitHubReader
from agent_graph.harness import FakeWorkerAdapter, GraphHarness
from agent_graph.observation import ObservableFact
from agent_graph.reconciler import GraphReconciler
from agent_graph.scheduler import GraphScheduler
from agent_graph.sqlite_store import SCHEMA_VERSION, SqliteControlPlaneStore


class Phase1DEffectSchedulerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "g.sqlite"
        self.store = SqliteControlPlaneStore(str(self.db))
        self.rt = DurableGraphRuntime(self.store)
        self.harness = GraphHarness(self.rt)
        self.head = "b" * 40
        self.base = "a" * 40

    def tearDown(self) -> None:
        self.rt.close()
        self.tmp.cleanup()

    def _to_approved(self) -> str:
        run = self.rt.create_run(
            objective="effect", project="portfolio-ops", base_sha=self.base, risk_tier="R1"
        )
        w = FakeWorkerAdapter(head_sha=self.head)
        for _ in range(3):
            self.assertTrue(self.harness.step(run.run_id, worker=w, write_context=False).apply.accepted)
        out = self.rt.grant_founder_approval(
            run_id=run.run_id, action="merge", head_sha=self.head, actor="agent-operator"
        )
        self.assertTrue(out["accepted"], out)
        return run.run_id

    def test_schema_v7(self) -> None:
        self.assertEqual(SCHEMA_VERSION, 7)

    def test_deploy_forbidden(self) -> None:
        with self.assertRaises(PermissionError):
            assert_effect_allowed(action="deploy", repo="jerry200176-png/portfolio-ops")
        with self.assertRaises(PermissionError):
            assert_effect_allowed(action="github_pr_merge", repo="jerry200176-png/AllTrue_System")

    def test_effect_merge_idempotent_and_consumes_approval(self) -> None:
        run_id = self._to_approved()
        mut = FakeGitHubMutator()
        a = self.rt.execute_approved_effect(
            run_id=run_id,
            action="github_pr_merge",
            repo="jerry200176-png/portfolio-ops",
            target="pr/42",
            mutator=mut,
            params={"pr_number": 42},
            observed_head_sha=self.head,
        )
        self.assertTrue(a["accepted"], a)
        self.assertTrue(a["approval_consumed"])
        self.assertEqual(len(mut.merges), 1)
        b = self.rt.execute_approved_effect(
            run_id=run_id,
            action="github_pr_merge",
            repo="jerry200176-png/portfolio-ops",
            target="pr/42",
            mutator=mut,
            params={"pr_number": 42},
            observed_head_sha=self.head,
        )
        self.assertTrue(b["accepted"])
        self.assertTrue(b.get("duplicate"))
        self.assertEqual(len(mut.merges), 1)
        approvals = self.store.list_approvals(run_id)
        self.assertTrue(any(x.status == "consumed" for x in approvals))

    def test_toctou_head_mismatch_fail_closed(self) -> None:
        run_id = self._to_approved()
        out = self.rt.execute_approved_effect(
            run_id=run_id,
            action="github_pr_comment",
            repo="jerry200176-png/portfolio-ops",
            target="pr/1",
            mutator=FakeGitHubMutator(),
            params={"pr_number": 1, "body": "x"},
            observed_head_sha="f" * 40,
        )
        self.assertFalse(out["accepted"])
        self.assertEqual(out["blocker"], "toctou_head_mismatch")

    def test_ambiguous_effect_requires_reconcile(self) -> None:
        run_id = self._to_approved()
        mut = FakeGitHubMutator(merge_ambiguous=True)
        out = self.rt.execute_approved_effect(
            run_id=run_id,
            action="github_pr_merge",
            repo="jerry200176-png/portfolio-ops",
            target="pr/7",
            mutator=mut,
            params={"pr_number": 7},
            observed_head_sha=self.head,
        )
        self.assertFalse(out["accepted"])
        eff = self.store.list_effects(run_id)[0]
        self.assertEqual(eff.status, "ambiguous")

    def test_reconcile_closes_after_external_merge(self) -> None:
        run_id = self._to_approved()
        # Simulate successful local effect then external merge observation.
        mut = FakeGitHubMutator()
        self.rt.execute_approved_effect(
            run_id=run_id,
            action="github_pr_merge",
            repo="jerry200176-png/portfolio-ops",
            target="pr/9",
            mutator=mut,
            params={"pr_number": 9},
            observed_head_sha=self.head,
        )
        reader = FakeGitHubReader(
            {
                "number": 9,
                "url": "https://example.invalid/pr/9",
                "state": "MERGED",
                "mergedAt": "2026-09-15T01:00:00Z",
                "mergeable": "UNKNOWN",
                "headRefOid": self.head,
                "statusCheckRollup": [
                    {"name": "validate", "status": "COMPLETED", "conclusion": "SUCCESS"}
                ],
            }
        )
        rec = GraphReconciler(self.rt, reader)
        out = rec.reconcile_run(run_id, pr_number=9, repo="jerry200176-png/portfolio-ops")
        self.assertTrue(out.closed, out.to_dict())
        final = self.rt.get_run(run_id)
        self.assertEqual(final.status, "closed_success")
        self.assertEqual(final.current_node, "close")

    def test_scheduler_tick_advances_worker_nodes(self) -> None:
        run = self.rt.create_run(objective="sched", project="portfolio-ops", base_sha=self.base)
        sched = GraphScheduler(self.rt, head_sha=self.head)
        t1 = sched.tick(limit=5)
        self.assertGreaterEqual(t1.examined, 1)
        run2 = self.rt.get_run(run.run_id)
        self.assertEqual(run2.current_node, "builder")

    def test_crash_executing_then_reconcile(self) -> None:
        run_id = self._to_approved()
        from agent_graph.effect_journal import DurableEffectJournal

        journal = DurableEffectJournal(self.store, FakeGitHubMutator())
        eff = journal.declare(
            run_id=run_id,
            action="github_pr_merge",
            repo="jerry200176-png/portfolio-ops",
            target="pr/3",
            head_sha=self.head,
        )
        journal.prepare(eff.effect_id, precheck={})
        journal.begin_execute(eff.effect_id)
        stuck = self.store.get_effect(eff.effect_id)
        self.assertEqual(stuck.status, "executing")
        reader = FakeGitHubReader(
            {
                "number": 3,
                "state": "MERGED",
                "mergedAt": "2026-09-15T01:00:00Z",
                "headRefOid": self.head,
                "url": "u",
                "statusCheckRollup": [],
            }
        )
        GraphReconciler(self.rt, reader).reconcile_run(run_id, pr_number=3)
        fixed = self.store.get_effect(eff.effect_id)
        self.assertEqual(fixed.status, "succeeded")


if __name__ == "__main__":
    unittest.main()
