"""Tests for Agent Graph Runtime v0 (stdlib unittest only)."""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from typing import Any, Optional

ROOT = Path(__file__).resolve().parents[1]
import sys

sys.path.insert(0, str(ROOT))

from agent_graph.dry_run import HEAD_V2, run_happy_path
from agent_graph.models import MAX_RETRIES_PER_NODE, MAX_TOTAL_AGENT_RUNS, Event
from agent_graph.reducer import can_close_successfully, reduce
from agent_graph.runtime import GraphRuntime
from agent_graph.store import AppendOnlyEventStore


def ev(
    event_id: str,
    event_type: str,
    node: str,
    actor_id: str,
    actor_role: str,
    task_id: str = "t1",
    head_sha: Optional[str] = "h1",
    base_sha: str = "b1",
    conclusion: Optional[str] = "ok",
    evidence: Optional[dict[str, Any]] = None,
    timestamp: str = "2026-07-27T00:00:00Z",
    repository: str = "jerry200176-png/portfolio-ops",
) -> Event:
    return Event(
        event_id=event_id,
        task_id=task_id,
        timestamp=timestamp,
        event_type=event_type,
        node=node,
        actor_id=actor_id,
        actor_role=actor_role,
        repository=repository,
        base_sha=base_sha,
        head_sha=head_sha,
        conclusion=conclusion,
        evidence=evidence or {},
    )


class GraphRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.rt = GraphRuntime()

    def _create(self) -> None:
        r = self.rt.apply(
            ev("e1", "TASK_CREATED", "intake", "system", "system", head_sha="b1")
        )
        self.assertTrue(r.accepted)
        self.assertEqual(r.state.current_node, "investigator")

    def _investigate(self) -> None:
        r = self.rt.apply(
            ev(
                "e2",
                "INVESTIGATION_COMPLETED",
                "investigator",
                "inv-1",
                "investigator",
                head_sha="b1",
            )
        )
        self.assertTrue(r.accepted)
        self.assertEqual(r.state.current_node, "builder")

    def _build(self, eid: str, actor: str, head: str) -> None:
        r = self.rt.apply(
            ev(eid, "BUILD_COMPLETED", "builder", actor, "builder", head_sha=head)
        )
        self.assertTrue(r.accepted, r.reason)

    def test_normal_transition_happy_path(self) -> None:
        out = run_happy_path()
        final = out["final_state"]
        self.assertEqual(final["task_status"], "closed_success")
        self.assertEqual(final["current_node"], "close")
        self.assertEqual(final["approved_head_sha"], HEAD_V2)
        self.assertTrue(final["human_approved"])
        self.assertNotEqual(final["builder_actor_id"], final["reviewer_actor_id"])
        self.assertEqual(out["external_agents_created"], 0)
        self.assertFalse(out["credential_exposed"])
        self.assertEqual(len(out["event_trace"]), 7)

    def test_illegal_transition_rejected(self) -> None:
        self._create()
        # Skip investigator — jump to BUILD_COMPLETED
        r = self.rt.apply(
            ev("bad", "BUILD_COMPLETED", "builder", "b1", "builder", head_sha="h1")
        )
        self.assertFalse(r.accepted)
        self.assertIn("illegal transition", r.reason or "")
        self.assertEqual(len(self.rt.store), 1)

    def test_duplicate_event_idempotency(self) -> None:
        e = ev("e1", "TASK_CREATED", "intake", "system", "system", head_sha="b1")
        r1 = self.rt.apply(e)
        r2 = self.rt.apply(e)
        self.assertTrue(r1.accepted)
        self.assertTrue(r2.accepted)
        self.assertTrue(r2.duplicate)
        self.assertEqual(len(self.rt.store), 1)
        self.assertEqual(r1.state.snapshot(), r2.state.snapshot())

    def test_duplicate_event_id_conflicting_payload_rejected(self) -> None:
        self.rt.apply(ev("e1", "TASK_CREATED", "intake", "system", "system", head_sha="b1"))
        conflict = ev(
            "e1",
            "TASK_CREATED",
            "intake",
            "system",
            "system",
            head_sha="b1",
            conclusion="different",
        )
        r = self.rt.apply(conflict)
        self.assertFalse(r.accepted)
        self.assertTrue(r.duplicate)

    def test_builder_cannot_review_self(self) -> None:
        self._create()
        self._investigate()
        self._build("e3", "same-actor", "h1")
        r = self.rt.apply(
            ev(
                "e4",
                "REVIEW_APPROVED",
                "reviewer",
                "same-actor",
                "reviewer",
                head_sha="h1",
            )
        )
        self.assertFalse(r.accepted)
        self.assertEqual(r.blocker, "builder_reviewer_same_actor")
        self.assertEqual(len(self.rt.store), 3)

    def test_retry_exhaustion(self) -> None:
        self._create()
        # Fail investigator MAX_RETRIES_PER_NODE times, then one more is rejected
        for i in range(MAX_RETRIES_PER_NODE):
            r = self.rt.apply(
                ev(
                    f"fail-{i}",
                    "NODE_FAILED",
                    "investigator",
                    "inv-1",
                    "investigator",
                    head_sha="b1",
                    conclusion="error",
                    evidence={"failure_signature": f"sig-{i}"},
                )
            )
            self.assertTrue(r.accepted, r.reason)
            self.assertEqual(r.state.retry_count.get("investigator"), i + 1)

        r = self.rt.apply(
            ev(
                "fail-extra",
                "NODE_FAILED",
                "investigator",
                "inv-1",
                "investigator",
                head_sha="b1",
                conclusion="error",
                evidence={"failure_signature": "sig-extra"},
            )
        )
        self.assertFalse(r.accepted)
        self.assertEqual(r.blocker, "retry_exhausted:investigator")

    def test_identical_failure_twice_stops(self) -> None:
        self._create()
        r1 = self.rt.apply(
            ev(
                "f1",
                "NODE_FAILED",
                "investigator",
                "inv-1",
                "investigator",
                evidence={"failure_signature": "boom"},
            )
        )
        self.assertTrue(r1.accepted)
        r2 = self.rt.apply(
            ev(
                "f2",
                "NODE_FAILED",
                "investigator",
                "inv-1",
                "investigator",
                evidence={"failure_signature": "boom"},
            )
        )
        self.assertFalse(r2.accepted)
        self.assertEqual(r2.blocker, "duplicate_failure:boom")

    def test_agent_run_budget(self) -> None:
        self._create()
        # Consume budget with NODE_FAILED using unique signatures
        # TASK_CREATED does not count; each NODE_FAILED does
        for i in range(MAX_TOTAL_AGENT_RUNS):
            # Stay under per-node retry by rotating nodes via forced path:
            # only investigator is active — so we need to reset retries by
            # testing budget independently: use many unique failures up to
            # MAX_RETRIES then... actually investigator only allows 2 retries.
            # Budget test: advance through graph with many agent events.
            pass

        # Dedicated budget scenario: create a runtime and apply agent events
        # until budget is hit by cycling builder via review reject.
        rt = GraphRuntime()
        rt.apply(ev("b0", "TASK_CREATED", "intake", "system", "system"))
        rt.apply(
            ev(
                "b1",
                "INVESTIGATION_COMPLETED",
                "investigator",
                "inv",
                "investigator",
            )
        )
        # agent_run_count = 1 so far
        # Loop: build + reject until budget
        n = 0
        while True:
            n += 1
            head = f"h{n}"
            br = rt.apply(
                ev(
                    f"build-{n}",
                    "BUILD_COMPLETED",
                    "builder",
                    "builder-a",
                    "builder",
                    head_sha=head,
                )
            )
            if not br.accepted:
                self.assertEqual(br.blocker, "agent_run_budget_exhausted")
                self.assertGreaterEqual(rt.state_for("t1").agent_run_count, MAX_TOTAL_AGENT_RUNS)
                break
            rr = rt.apply(
                ev(
                    f"rej-{n}",
                    "REVIEW_REJECTED",
                    "reviewer",
                    "reviewer-a",
                    "reviewer",
                    head_sha=head,
                )
            )
            if not rr.accepted:
                self.assertEqual(rr.blocker, "agent_run_budget_exhausted")
                self.assertGreaterEqual(rt.state_for("t1").agent_run_count, MAX_TOTAL_AGENT_RUNS)
                break
            if n > MAX_TOTAL_AGENT_RUNS + 2:
                self.fail("budget never exhausted")

    def test_cannot_close_successfully_without_human_approval(self) -> None:
        self._create()
        self._investigate()
        self._build("e3", "builder-a", "h1")
        self.rt.apply(
            ev(
                "e4",
                "REVIEW_APPROVED",
                "reviewer",
                "reviewer-a",
                "reviewer",
                head_sha="h1",
            )
        )
        state = self.rt.state_for("t1")
        self.assertEqual(state.task_status, "human_approval_required")
        self.assertFalse(can_close_successfully(state))
        # Attempting to close via human reject yields blocked, not success
        r = self.rt.apply(
            ev(
                "e5",
                "HUMAN_REJECTED",
                "human_gate",
                "founder",
                "human",
                head_sha="h1",
            )
        )
        self.assertTrue(r.accepted)
        self.assertEqual(r.state.task_status, "closed_blocked")
        self.assertFalse(can_close_successfully(r.state))

    def test_head_sha_change_invalidates_old_approval(self) -> None:
        # Build a path to human approval, then simulate a new build event
        # by replaying reducer with an extra BUILD that changes head after approval
        # — approvals are invalidated when head changes before close.
        events = [
            ev("e1", "TASK_CREATED", "intake", "system", "system", head_sha="b1"),
            ev(
                "e2",
                "INVESTIGATION_COMPLETED",
                "investigator",
                "inv",
                "investigator",
                head_sha="b1",
            ),
            ev("e3", "BUILD_COMPLETED", "builder", "b", "builder", head_sha="h1"),
            ev(
                "e4",
                "REVIEW_APPROVED",
                "reviewer",
                "r",
                "reviewer",
                head_sha="h1",
            ),
            ev(
                "e5",
                "HUMAN_APPROVED",
                "human_gate",
                "founder",
                "human",
                head_sha="h1",
            ),
        ]
        # Direct reduce of a hypothetical post-approval head change is tested
        # via apply_event semantics: after human approve we're closed.
        # Test invalidation *before* close: approve at human gate requires matching head;
        # if head changed after REVIEW_APPROVED, human must approve new head.
        rt = GraphRuntime()
        for e in events[:4]:
            self.assertTrue(rt.apply(e).accepted)
        state = rt.state_for("t1")
        self.assertEqual(state.head_sha, "h1")
        self.assertEqual(state.task_status, "human_approval_required")

        # Reducer: any head_sha change clears prior human approval
        from agent_graph.reducer import apply_event

        state.human_approved = True
        state.approved_head_sha = "h1"
        invalidated = apply_event(
            state,
            ev(
                "eY",
                "BUILD_COMPLETED",
                "builder",
                "b",
                "builder",
                head_sha="h2",
            ),
        )
        self.assertIsNone(invalidated.approved_head_sha)
        self.assertFalse(invalidated.human_approved)
        self.assertFalse(can_close_successfully(invalidated))

        # Runtime: HUMAN_APPROVED with wrong/stale head_sha is rejected
        r = rt.apply(
            ev(
                "e5",
                "HUMAN_APPROVED",
                "human_gate",
                "founder",
                "human",
                head_sha="stale-sha",
            )
        )
        self.assertFalse(r.accepted)
        self.assertIn("does not match", r.reason or "")

    def test_event_replay_rebuilds_same_state(self) -> None:
        out = run_happy_path()
        events = [Event.from_dict(d) for d in out["event_trace"]]
        s1 = reduce(events)
        s2 = reduce(events)
        self.assertEqual(s1.snapshot(), s2.snapshot())
        self.assertEqual(s1.snapshot(), out["final_state"])

        # Fresh runtime replaying the same appends
        rt = GraphRuntime()
        for e in events:
            self.assertTrue(rt.apply(e).accepted)
        self.assertEqual(rt.replay(events[0].task_id).snapshot(), s1.snapshot())

    def test_append_only_store_forbids_overwrite(self) -> None:
        store = AppendOnlyEventStore()
        e = ev("e1", "TASK_CREATED", "intake", "system", "system")
        store.append(e)
        with self.assertRaises(ValueError):
            store.overwrite(e)
        with self.assertRaises(ValueError):
            store.replace_all([e])

    def test_reviewer_cannot_merge(self) -> None:
        self._create()
        self._investigate()
        self._build("e3", "builder-a", "h1")
        r = self.rt.apply(
            ev(
                "e4",
                "REVIEW_APPROVED",
                "reviewer",
                "reviewer-a",
                "reviewer",
                head_sha="h1",
                conclusion="merge",
            )
        )
        self.assertFalse(r.accepted)
        self.assertEqual(r.blocker, "reviewer_merge_forbidden")

    def test_dry_run_module_main_exits_zero(self) -> None:
        import io
        from contextlib import redirect_stdout

        from agent_graph import dry_run

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = dry_run.main()
        self.assertEqual(code, 0)
        self.assertIn("closed_success", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
