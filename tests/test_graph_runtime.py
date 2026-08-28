"""Tests for Agent Graph Runtime v0 (stdlib unittest only)."""

from __future__ import annotations

import unittest
from pathlib import Path
from typing import Any, Optional

ROOT = Path(__file__).resolve().parents[1]
import sys

sys.path.insert(0, str(ROOT))

from agent_graph import dry_run
from agent_graph.dry_run import HEAD_V2, run_happy_path, run_stop_path
from agent_graph.models import MAX_RETRIES_PER_NODE, MAX_TOTAL_AGENT_RUNS, Event, TaskState
from agent_graph.reducer import apply_event, can_close_successfully, reduce
from agent_graph.router import validate_transition
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

    def _create(self, *, head_sha: Optional[str] = "b1") -> None:
        r = self.rt.apply(ev("e1", "TASK_CREATED", "intake", "system", "system", head_sha=head_sha))
        self.assertTrue(r.accepted)
        self.assertEqual(r.state.current_node, "investigator")

    def _investigate(self, *, head_sha: Optional[str] = "b1") -> None:
        r = self.rt.apply(
            ev("e2", "INVESTIGATION_COMPLETED", "investigator", "inv-1", "investigator", head_sha=head_sha)
        )
        self.assertTrue(r.accepted)
        self.assertEqual(r.state.current_node, "builder")

    def _build(self, eid: str, actor: str, head: str) -> None:
        r = self.rt.apply(ev(eid, "BUILD_COMPLETED", "builder", actor, "builder", head_sha=head))
        self.assertTrue(r.accepted, r.reason)

    def _review_approved(self, eid: str, actor: str, head: str) -> None:
        r = self.rt.apply(ev(eid, "REVIEW_APPROVED", "reviewer", actor, "reviewer", head_sha=head))
        self.assertTrue(r.accepted, r.reason)

    def _assert_stopped_state(self, state: Any, blocker: str, node: str) -> None:
        self.assertEqual(state.task_status, "blocked")
        self.assertTrue(state.stopped)
        self.assertEqual(state.blocker, blocker)
        self.assertEqual(state.current_node, node)

    def test_normal_transition_happy_path(self) -> None:
        out = run_happy_path()
        final = out["final_state"]
        self.assertEqual(final["task_status"], "closed_success")
        self.assertEqual(final["current_node"], "close")
        self.assertEqual(final["approved_head_sha"], HEAD_V2)
        self.assertTrue(final["human_approved"])
        self.assertFalse(final["stopped"])
        self.assertNotEqual(final["builder_actor_id"], final["reviewer_actor_id"])
        self.assertEqual(out["external_agents_created"], 0)
        self.assertFalse(out["credential_exposed"])
        self.assertEqual(len(out["event_trace"]), 7)

    def test_illegal_transition_rejected(self) -> None:
        self._create()
        r = self.rt.apply(ev("bad", "BUILD_COMPLETED", "builder", "b1", "builder", head_sha="h1"))
        self.assertFalse(r.accepted)
        self.assertIn("illegal transition", r.reason or "")
        self.assertEqual(len(self.rt.store), 1)

    def test_duplicate_event_idempotency(self) -> None:
        event = ev("e1", "TASK_CREATED", "intake", "system", "system", head_sha="b1")
        r1 = self.rt.apply(event)
        r2 = self.rt.apply(event)
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
        r = self.rt.apply(ev("e4", "REVIEW_APPROVED", "reviewer", "same-actor", "reviewer", head_sha="h1"))
        self.assertFalse(r.accepted)
        self.assertEqual(r.blocker, "builder_reviewer_same_actor")
        self.assertEqual(len(self.rt.store), 3)

    def test_build_completed_without_head_sha_rejected(self) -> None:
        self._create()
        self._investigate()
        r = self.rt.apply(ev("e3", "BUILD_COMPLETED", "builder", "builder-a", "builder", head_sha=None))
        self.assertFalse(r.accepted)
        self.assertEqual(r.reason, "BUILD_COMPLETED requires non-empty head_sha")

    def test_build_completed_with_empty_head_sha_rejected(self) -> None:
        self._create()
        self._investigate()
        r = self.rt.apply(ev("e3", "BUILD_COMPLETED", "builder", "builder-a", "builder", head_sha=""))
        self.assertFalse(r.accepted)
        self.assertEqual(r.reason, "BUILD_COMPLETED requires non-empty head_sha")

    def test_human_approved_requires_existing_state_head_sha(self) -> None:
        state = TaskState(task_id="t1", current_node="human_gate", task_status="human_approval_required")
        event = ev("e5", "HUMAN_APPROVED", "human_gate", "founder", "human", head_sha="h1")
        check = validate_transition(state, event)
        self.assertFalse(check.accepted)
        self.assertEqual(check.reason, "HUMAN_APPROVED requires current non-empty state.head_sha")

    def test_human_approved_with_stale_head_sha_rejected(self) -> None:
        self._create()
        self._investigate()
        self._build("e3", "builder-a", "h1")
        self._review_approved("e4", "reviewer-a", "h1")
        r = self.rt.apply(ev("e5", "HUMAN_APPROVED", "human_gate", "founder", "human", head_sha="stale-sha"))
        self.assertFalse(r.accepted)
        self.assertIn("does not match", r.reason or "")

    def test_human_approved_with_exact_current_head_sha_succeeds(self) -> None:
        self._create()
        self._investigate()
        self._build("e3", "builder-a", "h1")
        self._review_approved("e4", "reviewer-a", "h1")
        r = self.rt.apply(ev("e5", "HUMAN_APPROVED", "human_gate", "founder", "human", head_sha="h1"))
        self.assertTrue(r.accepted)
        self.assertTrue(r.state.human_approved)
        self.assertEqual(r.state.approved_head_sha, "h1")
        self.assertEqual(r.state.task_status, "closed_success")

    def test_head_sha_change_invalidates_old_approval(self) -> None:
        events = [
            ev("e1", "TASK_CREATED", "intake", "system", "system", head_sha="b1"),
            ev("e2", "INVESTIGATION_COMPLETED", "investigator", "inv", "investigator", head_sha="b1"),
            ev("e3", "BUILD_COMPLETED", "builder", "b", "builder", head_sha="h1"),
            ev("e4", "REVIEW_APPROVED", "reviewer", "r", "reviewer", head_sha="h1"),
        ]
        for event in events:
            self.assertTrue(self.rt.apply(event).accepted)

        state = self.rt.state_for("t1")
        self.assertEqual(state.head_sha, "h1")
        self.assertEqual(state.task_status, "human_approval_required")

        state.human_approved = True
        state.approved_head_sha = "h1"
        invalidated = apply_event(state, ev("eY", "BUILD_COMPLETED", "builder", "b", "builder", head_sha="h2"))
        self.assertIsNone(invalidated.approved_head_sha)
        self.assertFalse(invalidated.human_approved)
        self.assertFalse(can_close_successfully(invalidated))

    def test_retry_exhaustion_appends_graph_stopped(self) -> None:
        self._create()
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
        self._assert_stopped_state(r.state, "retry_exhausted:investigator", "investigator")
        trace = self.rt.event_trace("t1")
        self.assertEqual(trace[-1]["event_type"], "GRAPH_STOPPED")
        self.assertEqual(trace[-1]["evidence"]["retry_count"], MAX_RETRIES_PER_NODE)
        blocked = self.rt.state_for("t1")
        self._assert_stopped_state(blocked, "retry_exhausted:investigator", "investigator")

    def test_identical_failure_twice_appends_graph_stopped(self) -> None:
        self._create()
        self.assertTrue(
            self.rt.apply(
                ev(
                    "f1",
                    "NODE_FAILED",
                    "investigator",
                    "inv-1",
                    "investigator",
                    evidence={"failure_signature": "boom"},
                )
            ).accepted
        )
        r = self.rt.apply(
            ev(
                "f2",
                "NODE_FAILED",
                "investigator",
                "inv-1",
                "investigator",
                evidence={"failure_signature": "boom"},
            )
        )
        self.assertFalse(r.accepted)
        self.assertEqual(r.blocker, "duplicate_failure:boom")
        self._assert_stopped_state(r.state, "duplicate_failure:boom", "investigator")
        self.assertEqual(self.rt.event_trace("t1")[-1]["event_type"], "GRAPH_STOPPED")

    def test_agent_run_budget_appends_graph_stopped(self) -> None:
        self._create()
        self._investigate()
        n = 0
        while True:
            n += 1
            head = f"h{n}"
            br = self.rt.apply(ev(f"build-{n}", "BUILD_COMPLETED", "builder", "builder-a", "builder", head_sha=head))
            if not br.accepted:
                last = br
                break
            rr = self.rt.apply(
                ev(f"rej-{n}", "REVIEW_REJECTED", "reviewer", "reviewer-a", "reviewer", head_sha=head)
            )
            if not rr.accepted:
                last = rr
                break
        self.assertEqual(last.blocker, "agent_run_budget_exhausted")
        self._assert_stopped_state(last.state, "agent_run_budget_exhausted", "reviewer")
        self.assertEqual(self.rt.event_trace("t1")[-1]["event_type"], "GRAPH_STOPPED")
        self.assertEqual(self.rt.event_trace("t1")[-1]["evidence"]["agent_run_count"], MAX_TOTAL_AGENT_RUNS)

    def test_replay_preserves_blocked_state(self) -> None:
        out = run_stop_path()
        events = [Event.from_dict(data) for data in out["event_trace"]]
        reduced = reduce(events)
        self.assertEqual(reduced.snapshot(), out["final_state"])
        self.assertEqual(out["final_state"], out["replayed_state"])
        self._assert_stopped_state(reduced, "duplicate_failure:repeatable-investigator-failure", "investigator")

    def test_stopped_replay_blocks_future_progress(self) -> None:
        out = run_stop_path()
        rt = GraphRuntime()
        for data in out["event_trace"]:
            applied = rt.apply(Event.from_dict(data))
            self.assertTrue(applied.accepted or applied.duplicate)
        state = rt.replay("task-dry-run-001")
        self._assert_stopped_state(state, "duplicate_failure:repeatable-investigator-failure", "investigator")
        r = rt.apply(
            ev(
                "after-stop",
                "INVESTIGATION_COMPLETED",
                "investigator",
                "inv-1",
                "investigator",
                task_id="task-dry-run-001",
                head_sha="b1",
            )
        )
        self.assertFalse(r.accepted)
        self.assertIn("task blocked", r.reason or "")

    def test_duplicate_trigger_event_does_not_add_second_stop(self) -> None:
        self._create()
        self.assertTrue(
            self.rt.apply(
                ev(
                    "f1",
                    "NODE_FAILED",
                    "investigator",
                    "inv-1",
                    "investigator",
                    evidence={"failure_signature": "boom"},
                )
            ).accepted
        )
        first = self.rt.apply(
            ev(
                "f2",
                "NODE_FAILED",
                "investigator",
                "inv-1",
                "investigator",
                evidence={"failure_signature": "boom"},
            )
        )
        second = self.rt.apply(
            ev(
                "f2",
                "NODE_FAILED",
                "investigator",
                "inv-1",
                "investigator",
                evidence={"failure_signature": "boom"},
            )
        )
        self.assertFalse(first.accepted)
        self.assertFalse(second.accepted)
        trace = self.rt.event_trace("t1")
        self.assertEqual(sum(1 for item in trace if item["event_type"] == "GRAPH_STOPPED"), 1)

    def test_cannot_close_successfully_without_human_approval(self) -> None:
        self._create()
        self._investigate()
        self._build("e3", "builder-a", "h1")
        self._review_approved("e4", "reviewer-a", "h1")
        state = self.rt.state_for("t1")
        self.assertEqual(state.task_status, "human_approval_required")
        self.assertFalse(can_close_successfully(state))
        r = self.rt.apply(ev("e5", "HUMAN_REJECTED", "human_gate", "founder", "human", head_sha="h1"))
        self.assertTrue(r.accepted)
        self.assertEqual(r.state.task_status, "closed_blocked")
        self.assertFalse(can_close_successfully(r.state))

    def test_event_replay_rebuilds_same_state(self) -> None:
        out = run_happy_path()
        events = [Event.from_dict(data) for data in out["event_trace"]]
        s1 = reduce(events)
        s2 = reduce(events)
        self.assertEqual(s1.snapshot(), s2.snapshot())
        self.assertEqual(s1.snapshot(), out["final_state"])

        rt = GraphRuntime()
        for event in events:
            self.assertTrue(rt.apply(event).accepted)
        self.assertEqual(rt.replay(events[0].task_id).snapshot(), s1.snapshot())

    def test_append_only_store_forbids_overwrite(self) -> None:
        store = AppendOnlyEventStore()
        event = ev("e1", "TASK_CREATED", "intake", "system", "system")
        store.append(event)
        with self.assertRaises(ValueError):
            store.overwrite(event)
        with self.assertRaises(ValueError):
            store.replace_all([event])

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

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = dry_run.main()
        self.assertEqual(code, 0)
        output = buf.getvalue()
        self.assertIn("closed_success", output)
        self.assertIn("GRAPH_STOPPED", output)


if __name__ == "__main__":
    unittest.main()
