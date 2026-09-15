#!/usr/bin/env python3
"""High-value fault injection for autonomous scheduler (local evidence)."""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from agent_graph.durable_runtime import DurableGraphRuntime
from agent_graph.github_mutate import FakeGitHubMutator
from agent_graph.github_observe import FakeGitHubReader
from agent_graph.harness import FakeWorkerAdapter, GraphHarness
from agent_graph.policy_gate import advance_human_gate_by_policy
from agent_graph.reconciler import GraphReconciler
from agent_graph.scheduler import AutonomousSchedulerLoop, GraphScheduler
from agent_graph.sqlite_store import SqliteControlPlaneStore


def _run_case(name: str, fn) -> dict:
    try:
        payload = fn()
        return {"case": name, "ok": True, "result": payload}
    except Exception as exc:  # noqa: BLE001
        return {"case": name, "ok": False, "error": str(exc)}


def main() -> int:
    evidence: list[dict] = []
    head = "b" * 40
    base = "a" * 40

    def _fresh():
        tmp = tempfile.TemporaryDirectory()
        db = Path(tmp.name) / "g.sqlite"
        store = SqliteControlPlaneStore(str(db))
        rt = DurableGraphRuntime(store)
        harness = GraphHarness(rt)
        return tmp, store, rt, harness

    def kill_between_ticks() -> dict:
        tmp, store, rt, harness = _fresh()
        try:
            run = rt.create_run(objective="fi", project="portfolio-ops", base_sha=base)
            loop = AutonomousSchedulerLoop(
                rt, poll_interval_sec=0.01, max_poll_interval_sec=0.02, sleep_fn=lambda _s: None
            )
            loop.acquire_ownership()
            loop.tick_once()
            loop.release_ownership()
            loop2 = AutonomousSchedulerLoop(
                rt, poll_interval_sec=0.01, max_poll_interval_sec=0.02, sleep_fn=lambda _s: None
            )
            loop2.acquire_ownership()
            loop2.tick_once()
            loop2.release_ownership()
            return {"run_id": run.run_id, "node": rt.get_run(run.run_id).current_node}
        finally:
            rt.close()
            tmp.cleanup()

    def after_effect_before_reconcile() -> dict:
        tmp, store, rt, harness = _fresh()
        try:
            run = rt.create_run(
                objective="eff", project="portfolio-ops", base_sha=base, risk_tier="R1"
            )
            w = FakeWorkerAdapter(head_sha=head)
            for _ in range(3):
                harness.step(run.run_id, worker=w, write_context=False)
            advance_human_gate_by_policy(rt, run.run_id)
            from agent_graph.effect_journal import DurableEffectJournal

            journal = DurableEffectJournal(store, FakeGitHubMutator())
            eff = journal.declare(
                run_id=run.run_id,
                action="github_pr_merge",
                repo="jerry200176-png/portfolio-ops",
                target="pr/11",
                head_sha=head,
            )
            journal.prepare(eff.effect_id, precheck={})
            journal.begin_execute(eff.effect_id)
            reader = FakeGitHubReader(
                {
                    "number": 11,
                    "state": "MERGED",
                    "mergedAt": "2026-09-15T01:00:00Z",
                    "headRefOid": head,
                    "url": "u",
                    "statusCheckRollup": [],
                }
            )
            sched = GraphScheduler(rt, reconciler=GraphReconciler(rt, reader), head_sha=head)
            out = sched._advance_approved_for_effect(run.run_id, pr_number=11)
            return {
                "effect_status": store.get_effect(eff.effect_id).status,
                "action": out["action"],
            }
        finally:
            rt.close()
            tmp.cleanup()

    def worker_timeout_scheduler_continues() -> dict:
        tmp, store, rt, harness = _fresh()
        try:
            run = rt.create_run(objective="timeout", project="portfolio-ops", base_sha=base)

            class BoomWorker(FakeWorkerAdapter):
                def execute(self, **kwargs):  # type: ignore[no-untyped-def]
                    raise TimeoutError("worker timed out")

            sched = GraphScheduler(rt, head_sha=head)
            tick1 = sched.tick(limit=1)
            loop = AutonomousSchedulerLoop(
                rt,
                poll_interval_sec=0.01,
                max_poll_interval_sec=0.02,
                sleep_fn=lambda _s: None,
            )
            loop.acquire_ownership()
            orig = sched._worker_for_run

            def _boom(run_obj):
                if run_obj.current_node == "investigator":
                    return BoomWorker(head_sha=head)
                return orig(run_obj)

            sched._worker_for_run = _boom  # type: ignore[method-assign]
            loop.scheduler = sched
            t = loop.tick_once()
            loop.release_ownership()
            loop2 = AutonomousSchedulerLoop(
                rt,
                poll_interval_sec=0.01,
                max_poll_interval_sec=0.02,
                sleep_fn=lambda _s: None,
            )
            loop2.acquire_ownership()
            t2 = loop2.tick_once()
            loop2.release_ownership()
            return {
                "first_actions": [a.get("action") for a in t.advanced],
                "second_actions": [a.get("action") for a in t2.advanced],
                "node": rt.get_run(run.run_id).current_node,
                "tick1_idle": tick1.idle,
            }
        finally:
            rt.close()
            tmp.cleanup()

    def observation_temp_failure() -> dict:
        tmp, store, rt, harness = _fresh()
        try:
            run = rt.create_run(
                objective="obs", project="portfolio-ops", base_sha=base, risk_tier="R1"
            )
            w = FakeWorkerAdapter(head_sha=head)
            for _ in range(3):
                harness.step(run.run_id, worker=w, write_context=False)
            advance_human_gate_by_policy(rt, run.run_id)
            mut = FakeGitHubMutator()
            create = rt.execute_approved_effect(
                run_id=run.run_id,
                action="github_pr_create",
                repo="jerry200176-png/portfolio-ops",
                target="branch/obs",
                mutator=mut,
                params={"title": "t", "body": "b", "head": "obs", "base": "main"},
                observed_head_sha=head,
            )
            assert create.get("accepted"), create
            calls = {"n": 0}

            class FlakyReader(FakeGitHubReader):
                def pr_view(self, repo: str, pr_number: int):  # type: ignore[override]
                    calls["n"] += 1
                    if calls["n"] == 1:
                        raise RuntimeError("github temporarily unavailable")
                    return super().pr_view(repo, pr_number)

            reader = FlakyReader(
                {
                    "number": 12,
                    "state": "OPEN",
                    "mergedAt": None,
                    "headRefOid": head,
                    "url": "u",
                    "statusCheckRollup": [
                        {"name": "ci", "state": "PENDING", "conclusion": None}
                    ],
                }
            )
            sched = GraphScheduler(
                rt, mutator=mut, reconciler=GraphReconciler(rt, reader), head_sha=head
            )
            t1 = sched.tick(limit=1)
            a1 = [x.get("action") for x in t1.advanced]
            t2 = sched.tick(limit=1)
            return {
                "first": a1,
                "second": [x.get("action") for x in t2.advanced],
                "calls": calls["n"],
            }
        finally:
            rt.close()
            tmp.cleanup()

    evidence.append(_run_case("kill_scheduler_between_ticks", kill_between_ticks))
    evidence.append(_run_case("after_effect_before_local_confirm", after_effect_before_reconcile))
    evidence.append(
        _run_case("worker_timeout_scheduler_continues", worker_timeout_scheduler_continues)
    )
    evidence.append(_run_case("observation_temp_failure", observation_temp_failure))

    out_dir = ROOT / "reports" / "2026-09-15" / "scheduler-fault-injection"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "results.json"
    path.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(evidence, indent=2))
    return 0 if all(x["ok"] for x in evidence) else 1


if __name__ == "__main__":
    sys.exit(main())
