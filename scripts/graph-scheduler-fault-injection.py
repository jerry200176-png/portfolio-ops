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
    tmp = tempfile.TemporaryDirectory()
    db = Path(tmp.name) / "g.sqlite"
    store = SqliteControlPlaneStore(str(db))
    rt = DurableGraphRuntime(store)
    harness = GraphHarness(rt)
    head = "b" * 40
    base = "a" * 40

    def kill_between_ticks() -> dict:
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

    def after_effect_before_reconcile() -> dict:
        run = rt.create_run(objective="eff", project="portfolio-ops", base_sha=base, risk_tier="R1")
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
        return {"effect_status": store.get_effect(eff.effect_id).status, "action": out["action"]}

    evidence.append(_run_case("kill_scheduler_between_ticks", kill_between_ticks))
    evidence.append(_run_case("after_effect_before_local_confirm", after_effect_before_reconcile))

    out_dir = ROOT / "reports" / "2026-09-15" / "scheduler-fault-injection"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "results.json"
    path.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(evidence, indent=2))
    rt.close()
    tmp.cleanup()
    return 0 if all(x["ok"] for x in evidence) else 1


if __name__ == "__main__":
    sys.exit(main())
