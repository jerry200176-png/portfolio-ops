#!/usr/bin/env python3
"""Schedule-driven RealCodex dogfood: Goal → autonomous loop → closed_success.

Uses GraphScheduler / AutonomousSchedulerLoop with RealCodexWorkerAdapter for
investigator+builder (no FakeWorker on implementation nodes). Founder does not
manage Codex terminals or manual schedule-tick.

Requires GRAPH_REAL_CODEX=1.
Exit: 0 success, 1 failure, 2 unset, 3 usage-limit dormant.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from agent_graph.canonical_paths import (
    assert_canonical_db_outside_worktree,
    default_canonical_db_path,
    ensure_canonical_db_parent,
)
from agent_graph.durable_runtime import DurableGraphRuntime
from agent_graph.github_mutate import GhCliMutator
from agent_graph.github_observe import GhCliReader
from agent_graph.reconciler import GraphReconciler
from agent_graph.scheduler import AutonomousSchedulerLoop
from agent_graph.sqlite_store import SqliteControlPlaneStore
from agent_graph.worktree_bind import create_worktree_via_agent_start


def _objective_for_run(run_id: str, marker_rel: str) -> str:
    return f"""R1 portfolio-ops maintenance (RealCodex end-to-end dogfood).

Run id: {run_id}
Marker path: {marker_rel}

Investigator node: confirm docs/agent-graph/ is the correct place for the marker.
Do not modify files yet. Write INVESTIGATION_COMPLETED to .agent-session/result.json
then stop.

Builder node: create {marker_rel} with short sections Objective, Date (UTC),
RealCodex path, Run id ({run_id}). Commit on the current branch only
(git add + git commit). Do NOT git push, open/merge PRs, deploy, or touch
production — the control plane owns branch publish and GitHub effects.
Write BUILD_COMPLETED with the new HEAD sha to .agent-session/result.json.

Reviewer/effects are control-plane owned after build.
"""


OBJECTIVE = _objective_for_run("RUN_ID_PLACEHOLDER", "docs/agent-graph/real-codex-e2e-marker.md")


def _save(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _git(worktree: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(worktree), *args], text=True).strip()


def main() -> int:
    if os.environ.get("GRAPH_REAL_CODEX") != "1":
        print("Set GRAPH_REAL_CODEX=1", file=sys.stderr)
        return 2

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    evidence_dir = ROOT / "reports" / stamp / "schedule-realcodex-dogfood"
    evidence_dir.mkdir(parents=True, exist_ok=True)

    db_path = ensure_canonical_db_parent(default_canonical_db_path())
    task_id = f"graph-sched-rc-dogfood-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    worktree = Path(
        create_worktree_via_agent_start(project="portfolio-ops", task_id=task_id, dry_run=True)
    )
    assert_canonical_db_outside_worktree(db_path, worktree)

    store = SqliteControlPlaneStore(str(db_path))
    rt = DurableGraphRuntime(store)
    reconciler = GraphReconciler(rt, GhCliReader())
    mutator = GhCliMutator()

    base_sha = _git(worktree, "rev-parse", "HEAD")
    branch = _git(worktree, "branch", "--show-current")
    stamp_compact = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    marker_rel = f"docs/agent-graph/real-codex-e2e-marker-{stamp_compact}.md"
    # Placeholder run id resolved after create; builder still sees unique marker path.
    preliminary = _objective_for_run("pending", marker_rel)
    run = rt.create_run(
        objective=preliminary,
        project="portfolio-ops",
        risk_tier="R1",
        success_condition="Marker merged via Effect Journal; Run closed_success",
        base_sha=base_sha,
        worktree=str(worktree),
        branch=branch or None,
        repository="jerry200176-png/portfolio-ops",
    )
    run_id = run.run_id
    # Persist the definitive objective (with run_id) for worker context / evidence.
    final_objective = _objective_for_run(run_id, marker_rel)
    store._conn.execute(
        "UPDATE goals SET objective=? WHERE goal_id=?",
        (final_objective, run.goal_id),
    )
    store._conn.commit()
    trace_marker = marker_rel

    trace: dict[str, Any] = {
        "mode": "schedule-run",
        "run_id": run_id,
        "goal_id": run.goal_id,
        "worktree": str(worktree),
        "branch": branch,
        "base_sha": base_sha,
        "marker": trace_marker,
        "ticks": [],
        "worker_path": "RealCodexWorkerAdapter via AutonomousSchedulerLoop",
    }

    # Live dogfood must outlast GitHub CI and optionally Codex quota reset.
    max_ticks = int(os.environ.get("GRAPH_DOGFOOD_MAX_TICKS", "240"))
    poll = float(os.environ.get("GRAPH_DOGFOOD_POLL", "5.0"))
    wall_deadline = time.time() + float(
        os.environ.get("GRAPH_DOGFOOD_WALL_SEC", str(100 * 3600))
    )
    sleeps: list[float] = []

    def _sleep(sec: float) -> None:
        sleeps.append(sec)
        # Cap per-sleep; with wait_ci idle backoff this still allows ~30–60+ min wall time.
        time.sleep(min(sec, float(os.environ.get("GRAPH_DOGFOOD_SLEEP_CAP", "45"))))

    def _sleep_quota(sec: float) -> None:
        """Longer sleeps while waiting for Codex quota (does not use the short CI cap)."""
        sleeps.append(sec)
        time.sleep(min(sec, float(os.environ.get("GRAPH_DOGFOOD_QUOTA_SLEEP_CAP", "3600"))))

    loop = AutonomousSchedulerLoop(
        rt,
        reconciler=reconciler,
        mutator=mutator,
        project="portfolio-ops",
        poll_interval_sec=poll,
        max_poll_interval_sec=float(os.environ.get("GRAPH_DOGFOOD_MAX_POLL", "45")),
        lease_ttl_sec=120.0,
        tick_limit=3,
        use_real_codex=True,
        codex_timeout_sec=float(os.environ.get("GRAPH_REAL_CODEX_TIMEOUT", "1200")),
        canonical_db_path=str(db_path),
        sleep_fn=_sleep,
    )
    if not loop.acquire_ownership():
        trace["blocker"] = "scheduler_ownership_denied"
        _save(evidence_dir / "SUMMARY.json", trace)
        return 1

    # Dogfood must not be aborted by unrelated runnable Runs in the same DB.
    loop.focus_run_ids = {run_id}

    try:
        for i in range(max_ticks):
            if time.time() > wall_deadline:
                final = rt.get_run(run_id)
                trace["blocker"] = "wall_deadline_exhausted"
                trace["final"] = final.to_dict()
                _save(evidence_dir / "SUMMARY.json", {**trace, "closed_success": False, "exit_code": 1})
                return 1

            tick = loop.tick_once()
            trace["ticks"].append(tick.to_dict())
            _save(evidence_dir / "trace-partial.json", trace)

            hard_fail = next(
                (
                    a
                    for a in tick.advanced
                    if a.get("run_id") == run_id
                    and a.get("action")
                    in ("branch_push_failed", "pr_create_failed", "effect_blocked")
                ),
                None,
            )
            if hard_fail is not None:
                trace["blocker"] = hard_fail.get("blocker") or hard_fail.get("action")
                trace["hard_fail"] = hard_fail
                _save(evidence_dir / "SUMMARY.json", {**trace, "closed_success": False, "exit_code": 1})
                _save(evidence_dir / "trace-failed.json", trace)
                return 1

            ours_limited = any(
                a.get("action") == "dormant_codex_usage_limit" and a.get("run_id") == run_id
                for a in tick.advanced
            )
            if ours_limited:
                # Wait through quota window (scheduler already recorded resume epoch).
                resume = loop._codex_dormant_until.get(run_id)
                if resume is None:
                    env_epoch = os.environ.get("GRAPH_CODEX_QUOTA_RESUME_EPOCH")
                    resume = float(env_epoch) if env_epoch else None
                trace["quota_wait"] = {
                    "at": datetime.now(timezone.utc).isoformat(),
                    "resume_epoch": resume,
                    "tick": i,
                }
                _save(evidence_dir / "trace-partial.json", trace)
                if resume is None:
                    trace["blocker"] = "codex_usage_limit"
                    _save(
                        evidence_dir / "SUMMARY.json",
                        {**trace, "closed_success": False, "exit_code": 3},
                    )
                    _save(evidence_dir / "trace-failed.json", trace)
                    return 3
                wait_for = max(5.0, resume - time.time())
                _sleep_quota(wait_for)
                continue

            # Still inside recorded quota dormancy (skipped ticks) — keep waiting.
            if run_id in loop._codex_dormant_until:
                resume = loop._codex_dormant_until[run_id]
                _sleep_quota(max(5.0, resume - time.time()))
                continue

            final = rt.get_run(run_id)
            if final.status == "closed_success" and final.closed:
                break
            if final.stopped or final.status in ("closed_blocked", "blocked"):
                trace["blocker"] = final.blocker or final.status
                _save(evidence_dir / "SUMMARY.json", {**trace, "closed_success": False, "exit_code": 1})
                return 1

            sleep_for = loop._next_sleep(tick)
            _sleep(sleep_for)
        else:
            final = rt.get_run(run_id)
            trace["blocker"] = "max_ticks_exhausted"
            trace["final"] = final.to_dict()
            _save(evidence_dir / "SUMMARY.json", {**trace, "closed_success": False, "exit_code": 1})
            return 1
    finally:
        loop.release_ownership()

    final = rt.get_run(run_id)
    attempts = store.list_attempts(run_id) if hasattr(store, "list_attempts") else []
    if not attempts:
        rows = store._conn.execute(
            "SELECT attempt_id, node, worker_type, worker_pid, status FROM attempts WHERE run_id=? ORDER BY started_at",
            (run_id,),
        ).fetchall()
        attempts = [dict(r) for r in rows]

    effects = [e.to_dict() for e in store.list_effects(run_id)]
    from agent_graph.dogfood_evidence import collect_dogfood_evidence

    evidence = collect_dogfood_evidence(
        runtime=rt,
        store=store,
        run_id=run_id,
        scheduler_id=loop.scheduler_id,
        mode="schedule-run",
    )
    summary = {
        "closed_success": final.status == "closed_success",
        "run_id": run_id,
        "goal_id": run.goal_id,
        "marker": trace_marker,
        "final_status": final.status,
        "final_node": final.current_node,
        "head_sha": final.head_sha,
        "branch": final.branch,
        "attempts": attempts,
        "effects": effects,
        "scheduler_id": loop.scheduler_id,
        "ticks": len(trace["ticks"]),
        "sleeps": sleeps,
        "worker_path": "RealCodexWorkerAdapter",
        "mode": "schedule-run",
        "evidence": evidence,
    }
    trace["summary"] = summary
    trace["events"] = [e.to_dict() for e in rt.list_events(run_id)]
    _save(evidence_dir / "trace.json", trace)
    _save(evidence_dir / "SUMMARY.json", summary)
    _save(evidence_dir / "EVIDENCE.json", evidence)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if final.status == "closed_success" else 1


if __name__ == "__main__":
    sys.exit(main())
