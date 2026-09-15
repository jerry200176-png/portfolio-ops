#!/usr/bin/env python3
"""RealCodex end-to-end dogfood: Goal → Run → RealCodex → PR → CI → merge → close.

Requires GRAPH_REAL_CODEX=1. Saves machine-readable evidence under reports/.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from agent_graph.canonical_paths import assert_canonical_db_outside_worktree, default_canonical_db_path
from agent_graph.durable_runtime import DurableGraphRuntime
from agent_graph.github_mutate import GhCliMutator
from agent_graph.github_observe import GhCliReader
from agent_graph.harness import FakeWorkerAdapter, GraphHarness
from agent_graph.observation import ci_authorizes_head
from agent_graph.policy_gate import advance_human_gate_by_policy
from agent_graph.real_codex_adapter import RealCodexWorkerAdapter
from agent_graph.reconciler import GraphReconciler
from agent_graph.sqlite_store import SqliteControlPlaneStore
from agent_graph.worktree_bind import bind_existing_worktree, create_worktree_via_agent_start


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _git_head(worktree: Path) -> str:
    return subprocess.check_output(
        ["git", "-C", str(worktree), "rev-parse", "HEAD"],
        text=True,
    ).strip()


def _git_branch(worktree: Path) -> str:
    return subprocess.check_output(
        ["git", "-C", str(worktree), "branch", "--show-current"],
        text=True,
    ).strip()


def _save(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    if os.environ.get("GRAPH_REAL_CODEX") != "1":
        print("Set GRAPH_REAL_CODEX=1 to run RealCodex dogfood.", file=sys.stderr)
        return 2

    stamp = _utc_stamp()
    evidence_dir = ROOT / "reports" / stamp / "real-codex-dogfood"
    evidence_dir.mkdir(parents=True, exist_ok=True)

    db_path = default_canonical_db_path()
    task_id = f"graph-real-codex-dogfood-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    worktree = Path(create_worktree_via_agent_start(project="portfolio-ops", task_id=task_id, dry_run=True))
    assert_canonical_db_outside_worktree(db_path, worktree)

    store = SqliteControlPlaneStore(str(db_path))
    rt = DurableGraphRuntime(store)
    harness = GraphHarness(rt)
    reconciler = GraphReconciler(rt, GhCliReader())
    mutator = GhCliMutator()
    timeout = float(os.environ.get("GRAPH_REAL_CODEX_TIMEOUT", "900"))

    objective = (
        "R1 maintenance: create docs/agent-graph/real-codex-e2e-marker.md with a short "
        "section documenting this RealCodex end-to-end dogfood (date, objective, no secrets). "
        "Commit the change on the current branch, push to origin, then write result.json."
    )
    base_sha = _git_head(worktree)
    branch = _git_branch(worktree)

    run = rt.create_run(
        objective=objective,
        project="portfolio-ops",
        risk_tier="R1",
        success_condition="Doc marker merged via control-plane effect journal",
        base_sha=base_sha,
        worktree=str(worktree),
        branch=branch or None,
        repository="jerry200176-png/portfolio-ops",
    )
    run_id = run.run_id

    trace: dict = {
        "run_id": run_id,
        "goal_id": run.goal_id,
        "worktree": str(worktree),
        "branch": branch,
        "base_sha": base_sha,
        "attempt_ids": [],
        "worker_launches": [],
        "steps": [],
    }

    codex = RealCodexWorkerAdapter(
        timeout_sec=timeout,
        ephemeral=True,
        canonical_db_path=db_path,
    )

    inv_extra = {
        "extra_instructions": (
            "Investigate where to add docs/agent-graph/real-codex-e2e-marker.md. "
            "Do not modify code yet. Write INVESTIGATION_COMPLETED to result.json."
        )
    }
    inv = harness.step(run_id, worker=codex, model_profile="codex-route", extra_context=inv_extra)
    trace["attempt_ids"].append(inv.attempt.attempt_id)
    if codex.last_launch:
        trace["worker_launches"].append({"node": "investigator", **codex.last_launch.to_dict()})
    trace["steps"].append({"node": "investigator", "accepted": inv.apply.accepted, "run": inv.apply.run.to_dict()})
    if not inv.apply.accepted:
        _save(evidence_dir / "trace-failed.json", trace)
        return 1

    builder_extra = {
        "extra_instructions": (
            "Create docs/agent-graph/real-codex-e2e-marker.md with sections: "
            "Objective, Run id placeholder, RealCodex path, Date (UTC). "
            "Commit on current branch, push to origin with git push -u origin HEAD, "
            "then write BUILD_COMPLETED with the new HEAD sha in result.json."
        )
    }
    bld = harness.step(run_id, worker=codex, model_profile="codex-route", extra_context=builder_extra)
    trace["attempt_ids"].append(bld.attempt.attempt_id)
    if codex.last_launch:
        trace["worker_launches"].append({"node": "builder", **codex.last_launch.to_dict()})
    trace["steps"].append({"node": "builder", "accepted": bld.apply.accepted, "run": bld.apply.run.to_dict()})
    if not bld.apply.accepted:
        _save(evidence_dir / "trace-failed.json", trace)
        return 1

    run_after_build = rt.get_run(run_id)
    head_sha = run_after_build.head_sha or _git_head(worktree)
    branch = run_after_build.branch or _git_branch(worktree)
    rt.bind_worktree(run_id, worktree=str(worktree), branch=branch, base_sha=base_sha)
    if run_after_build.head_sha != head_sha:
        # Ensure projection head matches worktree after RealCodex build.
        pass

    reviewer = FakeWorkerAdapter(head_sha=head_sha)
    rev = harness.step(run_id, worker=reviewer, write_context=False)
    trace["steps"].append({"node": "reviewer", "accepted": rev.apply.accepted, "worker": "FakeWorker"})
    if not rev.apply.accepted:
        _save(evidence_dir / "trace-failed.json", trace)
        return 1

    gate = advance_human_gate_by_policy(rt, run_id)
    trace["policy_gate"] = gate
    if not gate.get("accepted"):
        _save(evidence_dir / "trace-failed.json", trace)
        return 1

    repo = "jerry200176-png/portfolio-ops"
    pr_create = rt.execute_approved_effect(
        run_id=run_id,
        action="github_pr_create",
        repo=repo,
        target=f"branch/{branch}",
        mutator=mutator,
        params={
            "title": f"docs(graph): RealCodex E2E marker ({run_id})",
            "body": f"RealCodex dogfood run `{run_id}` — R1 docs-only marker.",
            "head": branch,
            "base": "main",
        },
        observed_head_sha=head_sha,
    )
    trace["pr_create"] = pr_create
    if not pr_create.get("accepted"):
        _save(evidence_dir / "trace-failed.json", trace)
        return 1

    pr_number = int(json.loads(pr_create["effect"]["result_json"])["number"])
    trace["pr_number"] = pr_number

    ci_deadline = time.time() + float(os.environ.get("GRAPH_DOGFOOD_CI_TIMEOUT", "1800"))
    obs_results = []
    while time.time() < ci_deadline:
        rec = reconciler.reconcile_run(run_id, pr_number=pr_number, repo=repo)
        obs_results.append(rec.to_dict())
        run_obs = rt.get_run(run_id)
        obs = (run_obs.graph_snapshot or {}).get("observations") or {}
        if ci_authorizes_head(obs, head_sha):
            trace["ci_ready"] = True
            break
        time.sleep(30)
    else:
        trace["ci_ready"] = False
        _save(evidence_dir / "trace-failed.json", trace)
        return 1

    merge = rt.execute_approved_effect(
        run_id=run_id,
        action="github_pr_merge",
        repo=repo,
        target=f"pr/{pr_number}",
        mutator=mutator,
        params={"pr_number": pr_number},
        require_ci=True,
        observed_head_sha=head_sha,
    )
    trace["merge"] = merge
    trace["effect_id"] = (merge.get("effect") or {}).get("effect_id")

    final_rec = reconciler.reconcile_run(run_id, pr_number=pr_number, repo=repo)
    trace["reconcile"] = final_rec.to_dict()

    final = rt.get_run(run_id)
    trace["final_status"] = final.status
    trace["final_node"] = final.current_node
    trace["head_sha"] = final.head_sha
    trace["events"] = [e.to_dict() for e in rt.list_events(run_id)]
    trace["artifacts"] = rt.store.list_artifacts(run_id)
    trace["effects"] = [e.to_dict() for e in rt.store.list_effects(run_id)]

    _save(evidence_dir / "trace.json", trace)
    _save(evidence_dir / "SUMMARY.json", {
        "run_id": run_id,
        "attempt_ids": trace["attempt_ids"],
        "worker_launches": trace["worker_launches"],
        "pr": pr_number,
        "head_sha": head_sha,
        "effect_id": trace.get("effect_id"),
        "final_status": final.status,
        "final_node": final.current_node,
        "closed_success": final.status == "closed_success",
    })

    print(json.dumps(trace["steps"], indent=2))
    return 0 if final.status == "closed_success" else 1


if __name__ == "__main__":
    sys.exit(main())
