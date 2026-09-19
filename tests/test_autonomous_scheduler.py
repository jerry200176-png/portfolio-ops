"""Autonomous scheduler loop, ownership, and policy gate tests."""

from __future__ import annotations

import os
import json
import signal
import subprocess
import tempfile
import textwrap
import time
import unittest
from pathlib import Path
from unittest import mock

from agent_graph.durable_runtime import DurableGraphRuntime
from agent_graph.github_mutate import FakeGitHubMutator
from agent_graph.github_observe import FakeGitHubReader
from agent_graph.harness import FakeWorkerAdapter, GraphHarness
from agent_graph.policy_gate import advance_human_gate_by_policy
from agent_graph.reconciler import GraphReconciler
from agent_graph.scheduler import AutonomousSchedulerLoop, GraphScheduler
from agent_graph.scheduler_ownership import SchedulerOwnership
from agent_graph.sqlite_store import (
    LeaseBusyError,
    PreviousWorkerStillAliveError,
    SqliteControlPlaneStore,
)


class AutonomousSchedulerTests(unittest.TestCase):
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

    def _to_human_gate(self, *, risk_tier: str = "R1") -> str:
        run = self.rt.create_run(
            objective="sched",
            project="portfolio-ops",
            base_sha=self.base,
            risk_tier=risk_tier,
        )
        w = FakeWorkerAdapter(head_sha=self.head)
        for _ in range(3):
            self.assertTrue(
                self.harness.step(run.run_id, worker=w, write_context=False).apply.accepted
            )
        run2 = self.rt.get_run(run.run_id)
        self.assertEqual(run2.current_node, "human_gate")
        return run.run_id

    def test_policy_gate_advances_r1_without_founder(self) -> None:
        run_id = self._to_human_gate(risk_tier="R1")
        out = advance_human_gate_by_policy(self.rt, run_id)
        self.assertTrue(out["accepted"], out)
        run = self.rt.get_run(run_id)
        self.assertEqual(run.current_node, "approved_for_effect")

    def test_policy_gate_dormant_for_r3(self) -> None:
        run_id = self._to_human_gate(risk_tier="R3")
        out = advance_human_gate_by_policy(self.rt, run_id)
        self.assertFalse(out["accepted"])
        self.assertEqual(out.get("blocker"), "founder_approval_required")

    def test_pr_create_does_not_consume_merge_approval(self) -> None:
        run_id = self._to_human_gate(risk_tier="R1")
        advance_human_gate_by_policy(self.rt, run_id)
        mut = FakeGitHubMutator()
        create = self.rt.execute_approved_effect(
            run_id=run_id,
            action="github_pr_create",
            repo="jerry200176-png/portfolio-ops",
            target="branch/t",
            mutator=mut,
            params={"title": "t", "body": "b", "head": "t", "base": "main"},
            observed_head_sha=self.head,
        )
        self.assertTrue(create["accepted"], create)
        self.assertFalse(create.get("approval_consumed"))
        approvals = self.store.list_approvals(run_id)
        self.assertTrue(any(a.status == "granted" for a in approvals))

    def test_focus_run_ids_skips_other_runs(self) -> None:
        a = self.rt.create_run(objective="a", project="portfolio-ops", base_sha=self.base)
        b = self.rt.create_run(objective="b", project="portfolio-ops", base_sha=self.base)
        loop = AutonomousSchedulerLoop(
            self.rt,
            poll_interval_sec=0.01,
            max_poll_interval_sec=0.02,
            sleep_fn=lambda _s: None,
            tick_limit=5,
        )
        loop.focus_run_ids = {b.run_id}
        self.assertTrue(loop.acquire_ownership())
        try:
            tick = loop.tick_once()
            advanced_ids = {x.get("run_id") for x in tick.advanced}
            self.assertIn(b.run_id, advanced_ids)
            self.assertNotIn(a.run_id, advanced_ids)
        finally:
            loop.release_ownership()

    def test_second_scheduler_cannot_acquire_ownership(self) -> None:
        a = SchedulerOwnership(store=self.store, project="portfolio-ops", owner_id="sched_a")
        b = SchedulerOwnership(store=self.store, project="portfolio-ops", owner_id="sched_b")
        self.assertTrue(a.try_acquire())
        self.assertFalse(b.try_acquire())
        a.release()

    def test_scheduler_tick_advances_runnable_run(self) -> None:
        run = self.rt.create_run(objective="sched", project="portfolio-ops", base_sha=self.base)
        sched = GraphScheduler(self.rt, head_sha=self.head)
        out = sched.tick(limit=5)
        self.assertFalse(out.idle)
        self.assertEqual(self.rt.get_run(run.run_id).current_node, "builder")

    def test_waiting_for_approval_r3_not_busy_loop(self) -> None:
        run_id = self._to_human_gate(risk_tier="R3")
        sleeps: list[float] = []

        def _sleep(sec: float) -> None:
            sleeps.append(sec)

        loop = AutonomousSchedulerLoop(
            self.rt,
            poll_interval_sec=1.0,
            max_poll_interval_sec=5.0,
            sleep_fn=_sleep,
        )
        self.assertTrue(loop.acquire_ownership())
        try:
            tick = loop.tick_once()
            self.assertTrue(
                any(
                    x.get("action") == "dormant_waiting_for_approval"
                    for x in tick.advanced
                )
            )
            sleep_for = loop._next_sleep(tick)
            self.assertGreaterEqual(sleep_for, 1.0)
        finally:
            loop.release_ownership()

    def test_wait_effect_for_ci_counts_as_idle(self) -> None:
        """PR created but CI not green yet → wait_effect must backoff, not spin."""
        run_id = self._to_human_gate(risk_tier="R1")
        advance_human_gate_by_policy(self.rt, run_id)
        mut = FakeGitHubMutator()
        create = self.rt.execute_approved_effect(
            run_id=run_id,
            action="github_pr_create",
            repo="jerry200176-png/portfolio-ops",
            target="branch/ci-wait",
            mutator=mut,
            params={"title": "t", "body": "b", "head": "ci-wait", "base": "main"},
            observed_head_sha=self.head,
        )
        self.assertTrue(create.get("accepted"), create)
        pr_num = int(json.loads(create["effect"]["result_json"])["number"])
        # Align fake PR head with run head so TOCTOU/CI checks see a consistent SHA.
        reader_state = {
            "number": pr_num,
            "state": "OPEN",
            "mergedAt": None,
            "headRefOid": self.head,
            "url": "u",
            "statusCheckRollup": [
                {"name": "ci", "state": "PENDING", "conclusion": None}
            ],
        }
        reader = FakeGitHubReader(reader_state)
        sched = GraphScheduler(
            self.rt,
            mutator=mut,
            reconciler=GraphReconciler(self.rt, reader),
            head_sha=self.head,
        )
        out = sched.tick(limit=5)
        self.assertTrue(
            any(x.get("action") == "wait_ci" for x in out.advanced),
            out.advanced,
        )
        self.assertTrue(out.idle, out.advanced)

    def test_autonomous_loop_idle_backoff(self) -> None:
        sleeps: list[float] = []

        def _sleep(sec: float) -> None:
            sleeps.append(sec)

        loop = AutonomousSchedulerLoop(
            self.rt,
            poll_interval_sec=2.0,
            max_poll_interval_sec=30.0,
            sleep_fn=_sleep,
        )
        self.assertTrue(loop.acquire_ownership())
        try:
            t1 = loop.tick_once()
            self.assertTrue(t1.idle)
            s1 = loop._next_sleep(t1)
            t2 = loop.tick_once()
            s2 = loop._next_sleep(t2)
            self.assertGreater(s2, s1)
        finally:
            loop.release_ownership()

    def test_graceful_shutdown_releases_ownership(self) -> None:
        loop = AutonomousSchedulerLoop(self.rt, poll_interval_sec=0.01, max_poll_interval_sec=0.02)
        self.assertTrue(loop.acquire_ownership())
        active = self.store.get_active_lease(loop.ownership.resource_key)
        self.assertIsNotNone(active)
        loop.release_ownership()
        active2 = self.store.get_active_lease(loop.ownership.resource_key)
        self.assertIsNone(active2)

    def test_crash_restart_run_persists(self) -> None:
        run = self.rt.create_run(objective="persist", project="portfolio-ops", base_sha=self.base)
        run_id = run.run_id
        self.rt.close()
        store2 = SqliteControlPlaneStore(str(self.db))
        rt2 = DurableGraphRuntime(store2)
        try:
            restored = rt2.get_run(run_id)
            self.assertEqual(restored.objective if hasattr(restored, "objective") else restored.run_id, run_id)
            sched = GraphScheduler(rt2, head_sha=self.head)
            sched.tick(limit=1)
            self.assertEqual(rt2.get_run(run_id).current_node, "builder")
        finally:
            rt2.close()

    def test_worker_crash_scheduler_continues(self) -> None:
        run = self.rt.create_run(
            objective="worker-crash",
            project="portfolio-ops",
            base_sha=self.base,
            worktree=str(Path(self.tmp.name) / "wt"),
        )
        wt = Path(self.rt.get_run(run.run_id).worktree or "")
        wt.mkdir(parents=True, exist_ok=True)
        (wt / ".git").mkdir()

        class _Boom:
            worker_type = "codex"

            def execute(self, *, run, attempt, context):
                raise RuntimeError("simulated worker crash")

        sched = GraphScheduler(self.rt, use_real_codex=False, head_sha=self.head)
        try:
            sched.harness.step(run.run_id, worker=_Boom(), write_context=False)
        except RuntimeError:
            pass
        tick = sched.tick(limit=1)
        self.assertTrue(any(x.get("action") in ("step", "step_error") for x in tick.advanced))

    def test_ambiguous_effect_reconcile_no_duplicate_merge(self) -> None:
        run_id = self._to_human_gate(risk_tier="R1")
        advance_human_gate_by_policy(self.rt, run_id)
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
        reader = FakeGitHubReader(
            {
                "number": 7,
                "state": "MERGED",
                "mergedAt": "2026-09-15T01:00:00Z",
                "headRefOid": self.head,
                "url": "u",
                "statusCheckRollup": [],
            }
        )
        sched = GraphScheduler(self.rt, reconciler=GraphReconciler(self.rt, reader), head_sha=self.head)
        item = sched._advance_approved_for_effect(run_id, pr_number=7)
        self.assertIn(
            item["action"],
            (
                "reconcile_ambiguous_merge",
                "merge_and_reconcile",
                "reconcile_only",
                "reconcile_closed",
            ),
        )
        self.assertEqual(len(mut.merges), 0)

    def test_alive_owner_blocks_takeover(self) -> None:
        root = Path(self.tmp.name)
        marker = root / "orphan.marker"
        proc = subprocess.Popen(
            ["bash", "-c", f'while true; do echo x >> "{marker}"; sleep 0.2; done'],
            start_new_session=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        try:
            from agent_graph.process_identity import read_process_identity

            deadline = time.time() + 5
            while time.time() < deadline:
                if read_process_identity(proc.pid) is not None:
                    break
                time.sleep(0.05)

            resource = "scheduler:portfolio-ops"
            now = "2026-09-15T00:00:00Z"
            exp = "2026-09-15T00:00:01Z"
            token = self.store.acquire_execution_lease(
                resource_key=resource,
                attempt_id="sched_orphan",
                run_id="scheduler",
                node="loop",
                now=now,
                expires_at=exp,
                lease_id="lease_orphan",
            )
            ident = read_process_identity(proc.pid)
            self.assertIsNotNone(ident)
            self.store.bind_execution_identity(
                resource_key=resource,
                attempt_id="sched_orphan",
                fencing_token=int(token),
                identity=ident,
            )
            later = "2026-09-15T00:05:00Z"
            with self.assertRaises(PreviousWorkerStillAliveError):
                self.store.acquire_execution_lease(
                    resource_key=resource,
                    attempt_id="sched_takeover",
                    run_id="scheduler",
                    node="loop",
                    now=later,
                    expires_at="2026-09-15T00:05:30Z",
                    lease_id="lease_takeover",
                )
        finally:
            os.killpg(proc.pid, signal.SIGKILL)
            proc.wait(timeout=5)

    def test_loop_run_forever_max_ticks(self) -> None:
        run = self.rt.create_run(objective="loop", project="portfolio-ops", base_sha=self.base)
        loop = AutonomousSchedulerLoop(
            self.rt,
            poll_interval_sec=0.01,
            max_poll_interval_sec=0.02,
            sleep_fn=lambda _s: None,
        )
        code = loop.run_forever(max_ticks=3)
        self.assertEqual(code, 0)
        self.assertGreaterEqual(loop.status.ticks, 3)
        self.assertFalse(loop.status.ownership_held)
        self.assertEqual(self.rt.get_run(run.run_id).current_node, "human_gate")

    def test_codex_usage_limit_marks_run_dormant(self) -> None:
        """Usage-limit must not busy-loop: first hit dormants, later ticks skip."""
        wt = Path(self.tmp.name) / "wt-ul"
        wt.mkdir()
        (wt / ".git").mkdir()
        run = self.rt.create_run(
            objective="usage-limit",
            project="portfolio-ops",
            base_sha=self.base,
            worktree=str(wt),
        )
        route = Path(self.tmp.name) / "bin" / "codex-route-ul"
        route.parent.mkdir(parents=True, exist_ok=True)
        route.write_text(
            textwrap.dedent(
                """\
                #!/usr/bin/env bash
                set -euo pipefail
                for a in "$@"; do
                  if [[ "$a" == "--dry-run" ]]; then
                    echo '{"profile":"terra","model":"stub","reasoning_effort_override":null,"reason":"t","resolution":"selected","requested_tier":"terra","selected_tier":"terra"}'
                    exit 0
                  fi
                done
                echo 'ERROR: You have hit your usage limit.' >&2
                exit 1
                """
            ),
            encoding="utf-8",
        )
        route.chmod(route.stat().st_mode | 0o111)

        from agent_graph.real_codex_adapter import RealCodexWorkerAdapter

        class _Sched(GraphScheduler):
            def _worker_for_run(self, run):  # type: ignore[no-untyped-def]
                return RealCodexWorkerAdapter(
                    codex_route=str(route),
                    timeout_sec=10,
                    ephemeral=True,
                    canonical_db_path=self.canonical_db_path or str(self.runtime.store.path),
                )

        # SqliteControlPlaneStore may not expose .path — use db from test.
        sched = _Sched(self.rt, use_real_codex=True, canonical_db_path=str(self.db))
        # Monkeypatch worker factory
        def _worker(_run):
            return RealCodexWorkerAdapter(
                codex_route=str(route),
                timeout_sec=10,
                ephemeral=True,
                canonical_db_path=str(self.db),
            )

        sched._worker_for_run = _worker  # type: ignore[method-assign]
        loop = AutonomousSchedulerLoop(
            self.rt,
            poll_interval_sec=0.01,
            max_poll_interval_sec=0.05,
            sleep_fn=lambda _s: None,
            use_real_codex=True,
            canonical_db_path=str(self.db),
        )
        loop.scheduler = sched
        self.assertTrue(loop.acquire_ownership())
        try:
            t1 = loop.tick_once()
            self.assertTrue(
                any(x.get("action") == "dormant_codex_usage_limit" for x in t1.advanced),
                t1.to_dict(),
            )
            self.assertIn(run.run_id, loop._codex_dormant_until)
            self.assertNotIn(run.run_id, loop._permanent_blockers)
            t2 = loop.tick_once()
            # Skipped while dormant → idle
            self.assertTrue(t2.idle)
            self.assertEqual(t2.examined, 0)
            # After resume epoch, run is eligible again.
            loop._codex_dormant_until[run.run_id] = time.time() - 1
            t3 = loop.tick_once()
            self.assertTrue(
                any(x.get("run_id") == run.run_id for x in t3.advanced),
                t3.to_dict(),
            )
        finally:
            loop.release_ownership()

    def test_parse_codex_usage_resume_epoch(self) -> None:
        from agent_graph.real_codex_adapter import parse_codex_usage_resume_epoch

        detail = (
            "ERROR: You've hit your usage limit. Visit https://chatgpt.com/codex/"
            "settings/usage to purchase more credits or try again at Sep 19th, 2026 4:26 PM."
        )
        epoch = parse_codex_usage_resume_epoch(detail)
        self.assertIsNotNone(epoch)
        # 2026-09-19 16:26 Asia/Taipei == 08:26 UTC
        self.assertAlmostEqual(epoch or 0, 1789806360.0, delta=120)

    def test_codex_binary_missing_is_permanent_blocker(self) -> None:
        from agent_graph.real_codex_adapter import _read_codex_binary_missing

        log = Path(self.tmp.name) / "stderr.log"
        log.write_text(
            "FileNotFoundError: [Errno 2] No such file or directory: 'codex'\n",
            encoding="utf-8",
        )
        self.assertTrue(_read_codex_binary_missing(log))
        loop = AutonomousSchedulerLoop(
            self.rt, poll_interval_sec=0.01, max_poll_interval_sec=0.02, sleep_fn=lambda _s: None
        )
        from agent_graph.scheduler import ScheduleTickResult

        tick = ScheduleTickResult(
            examined=1,
            advanced=[
                {
                    "run_id": "run_missing",
                    "action": "codex_binary_missing",
                    "blocker": "codex_binary_missing",
                }
            ],
            idle=False,
        )
        loop._record_blockers(tick)
        self.assertIn("run_missing", loop._permanent_blockers)


if __name__ == "__main__":
    unittest.main()
