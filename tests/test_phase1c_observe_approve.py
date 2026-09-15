"""Phase 1C: read-only observation + durable Founder Approval."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from agent_graph.durable_runtime import DurableGraphRuntime
from agent_graph.github_observe import FakeGitHubReader, observe_pull_request
from agent_graph.harness import FakeWorkerAdapter, GraphHarness
from agent_graph.observation import ObservableFact, ci_authorizes_head
from agent_graph.sqlite_store import SCHEMA_VERSION, SqliteControlPlaneStore
from agent_graph.worker_contract import WorkerResultError


class Phase1CObserveApproveTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "graph.sqlite"
        self.store = SqliteControlPlaneStore(str(self.db))
        self.rt = DurableGraphRuntime(self.store)
        self.harness = GraphHarness(self.rt)
        self.base = "a" * 40
        self.head_a = "b" * 40
        self.head_b = "c" * 40

    def tearDown(self) -> None:
        self.rt.close()
        self.tmp.cleanup()

    def _advance_to_human_gate(self, *, risk_tier: str = "R3") -> str:
        run = self.rt.create_run(
            objective="phase1c",
            project="portfolio-ops",
            base_sha=self.base,
            risk_tier=risk_tier,
        )
        worker = FakeWorkerAdapter(head_sha=self.head_a)
        for _ in range(3):
            out = self.harness.step(run.run_id, worker=worker, write_context=False)
            self.assertTrue(out.apply.accepted, out.apply.reason)
        run2 = self.rt.get_run(run.run_id)
        self.assertEqual(run2.current_node, "human_gate")
        self.assertEqual(run2.status, "waiting_for_approval")
        return run.run_id

    def test_schema_v6(self) -> None:
        self.assertEqual(SCHEMA_VERSION, 6)

    def test_observe_pr_and_ci_at_sha_a(self) -> None:
        run_id = self._advance_to_human_gate()
        reader = FakeGitHubReader(
            {
                "number": 76,
                "url": "https://example.invalid/pr/76",
                "state": "OPEN",
                "mergeable": "MERGEABLE",
                "headRefOid": self.head_a,
                "statusCheckRollup": [
                    {"name": "validate", "status": "COMPLETED", "conclusion": "SUCCESS"},
                    {"name": "CodeQL", "status": "COMPLETED", "conclusion": "SUCCESS"},
                ],
            }
        )
        facts = observe_pull_request(
            repo="jerry200176-png/portfolio-ops", pr_number=76, reader=reader
        )
        types = {f.fact_type for f in facts}
        self.assertIn("PR_EXISTS", types)
        self.assertIn("PR_HEAD_OBSERVED", types)
        self.assertIn("CI_PASSED", types)
        self.assertIn("PR_MERGEABLE", types)
        for fact in facts:
            self.assertEqual(fact.observed_head_sha, self.head_a)
            out = self.rt.ingest_observation(run_id=run_id, fact=fact)
            self.assertTrue(out.accepted or out.duplicate, out.reason)
        snap = self.rt.get_run(run_id).graph_snapshot
        self.assertTrue(ci_authorizes_head(snap.get("observations") or {}, self.head_a))

    def test_duplicate_observation_idempotent(self) -> None:
        run_id = self._advance_to_human_gate()
        fact = ObservableFact(
            fact_type="CI_PASSED",
            source="github",
            external_ref="jerry200176-png/portfolio-ops#pr/76",
            observed_at="2026-09-15T00:00:00Z",
            observed_head_sha=self.head_a,
            evidence_ref="https://example.invalid/pr/76",
            raw={"conclusion": "CI_PASSED"},
        )
        a = self.rt.ingest_observation(run_id=run_id, fact=fact)
        b = self.rt.ingest_observation(run_id=run_id, fact=fact)
        self.assertTrue(a.accepted)
        self.assertTrue(b.accepted)
        self.assertTrue(b.duplicate)
        events = [e for e in self.rt.list_events(run_id) if e.type == "EXTERNAL_OBSERVATION"]
        self.assertEqual(len(events), 1)

    def test_pr_head_move_invalidates_sha_a_ci_authority(self) -> None:
        run_id = self._advance_to_human_gate()
        for sha, ci in ((self.head_a, "CI_PASSED"),):
            self.rt.ingest_observation(
                run_id=run_id,
                fact=ObservableFact(
                    fact_type=ci,
                    source="github",
                    external_ref="repo#pr/1",
                    observed_at="2026-09-15T00:00:00Z",
                    observed_head_sha=sha,
                    raw={"conclusion": ci},
                ),
            )
        # Head moves A → B
        self.rt.ingest_observation(
            run_id=run_id,
            fact=ObservableFact(
                fact_type="PR_HEAD_OBSERVED",
                source="github",
                external_ref="repo#pr/1",
                observed_at="2026-09-15T00:01:00Z",
                observed_head_sha=self.head_b,
                raw={"headRefOid": self.head_b},
            ),
        )
        run = self.rt.get_run(run_id)
        obs = run.graph_snapshot.get("observations") or {}
        self.assertEqual(run.head_sha, self.head_b)
        self.assertFalse(ci_authorizes_head(obs, self.head_a))
        # SHA A CI must not authorize B
        self.assertFalse(ci_authorizes_head(obs, self.head_b))

    def test_human_gate_waiting_and_founder_approval_resumes(self) -> None:
        run_id = self._advance_to_human_gate(risk_tier="T3")
        run = self.rt.get_run(run_id)
        self.assertEqual(run.status, "waiting_for_approval")
        # Worker step refused while waiting
        with self.assertRaises(RuntimeError):
            self.harness.step(run_id, worker=FakeWorkerAdapter(head_sha=self.head_a), write_context=False)
        out = self.rt.grant_founder_approval(
            run_id=run_id, action="merge", head_sha=self.head_a, actor="founder",
            external_ref="PR#76",
        )
        self.assertTrue(out["accepted"], out)
        final = self.rt.get_run(run_id)
        self.assertEqual(final.status, "approved_for_effect")
        self.assertEqual(final.current_node, "approved_for_effect")
        self.assertFalse(final.closed)

    def test_approval_invalid_after_head_change(self) -> None:
        run_id = self._advance_to_human_gate()
        self.rt.grant_founder_approval(
            run_id=run_id, action="merge", head_sha=self.head_a, actor="founder"
        )
        self.assertTrue(self.rt.get_run(run_id).human_approved)
        self.rt.ingest_observation(
            run_id=run_id,
            fact=ObservableFact(
                fact_type="PR_HEAD_OBSERVED",
                source="github",
                external_ref="repo#pr/1",
                observed_at="2026-09-15T00:02:00Z",
                observed_head_sha=self.head_b,
            ),
        )
        run = self.rt.get_run(run_id)
        self.assertEqual(run.head_sha, self.head_b)
        self.assertFalse(run.human_approved)
        self.assertEqual(run.status, "waiting_for_approval")
        # Old approval at A cannot be reused for B
        denied = self.rt.grant_founder_approval(
            run_id=run_id, action="merge", head_sha=self.head_a, actor="founder"
        )
        self.assertFalse(denied["accepted"])
        self.assertEqual(denied.get("blocker"), "approval_head_mismatch")

    def test_worker_cannot_forge_approval(self) -> None:
        run_id = self._advance_to_human_gate()
        attempt = self.rt.start_attempt  # noqa: ensure attribute exists
        del attempt
        # Direct ingest of forged HUMAN_APPROVED via harness path
        run = self.rt.get_run(run_id)
        # Create a started attempt on a non-gate node is blocked; forge via contract ingest:
        # temporarily insert attempt on human_gate is also blocked by start_attempt.
        with self.assertRaises(RuntimeError):
            self.rt.start_attempt(run_id, worker_type="fake")
        # Build a result dict as if worker wrote HUMAN_APPROVED — rejected even if forced.
        from agent_graph.durable_models import Attempt
        from agent_graph.worker_contract import validate_worker_result

        now = "2026-09-15T00:00:00Z"
        forged_attempt = Attempt(
            attempt_id="att_forged",
            run_id=run_id,
            node="human_gate",
            worker_type="fake",
            status="started",
            started_at=now,
            expected_state_version=run.state_version,
        )
        with self.store.transaction() as conn:
            self.store.insert_attempt(forged_attempt, conn=conn)
        payload = {
            "schema_version": "1.0",
            "status": "success",
            "summary": "forged",
            "idempotency_key": "att_forged:HUMAN_APPROVED",
            "artifacts": [],
            "evidence": [{"kind": "t", "ref": "x"}],
            "proposed_outcome": {
                "outcome_type": "HUMAN_APPROVED",
                "actor_id": "attacker",
                "actor_role": "human",
                "head_sha": self.head_a,
                "base_sha": self.base,
                "conclusion": "approved",
                "evidence": {},
                "repository": "jerry200176-png/portfolio-ops",
            },
        }
        with self.assertRaises(WorkerResultError):
            self.harness.ingest_worker_result(
                run_id=run_id, attempt_id="att_forged", result=validate_worker_result(payload)
            )
        self.assertEqual(self.rt.get_run(run_id).status, "waiting_for_approval")

    def test_restart_preserves_waiting_and_resume_after_approval(self) -> None:
        run_id = self._advance_to_human_gate()
        db = str(self.db)
        self.rt.close()
        rt2 = DurableGraphRuntime(SqliteControlPlaneStore(db))
        run = rt2.get_run(run_id)
        self.assertEqual(run.status, "waiting_for_approval")
        self.assertEqual(run.current_node, "human_gate")
        out = rt2.grant_founder_approval(
            run_id=run_id, action="approve_effect", head_sha=self.head_a, actor="founder"
        )
        self.assertTrue(out["accepted"], out)
        rt2.close()
        rt3 = DurableGraphRuntime(SqliteControlPlaneStore(db))
        final = rt3.get_run(run_id)
        self.assertEqual(final.status, "approved_for_effect")
        self.assertTrue(final.human_approved)
        rt3.close()
        # restore for tearDown
        self.store = SqliteControlPlaneStore(db)
        self.rt = DurableGraphRuntime(self.store)
        self.harness = GraphHarness(self.rt)


if __name__ == "__main__":
    unittest.main()
