#!/usr/bin/env python3
"""Real Codex A→B replaceability proof (explicit integration gate).

Requires network + authenticated Codex CLI. Does not touch other workers' PIDs.

Usage:
  GRAPH_REAL_CODEX=1 python3 scripts/graph-real-codex-proof.py

Evidence written under reports/<date>/real-codex-replaceable-worker/
"""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from agent_graph.durable_runtime import DurableGraphRuntime
from agent_graph.harness import GraphHarness
from agent_graph.real_codex_adapter import RealCodexWorkerAdapter, wait_pid_exited
from agent_graph.sqlite_store import SqliteControlPlaneStore
from agent_graph.worktree_bind import create_worktree_via_agent_start


def main() -> int:
    if os.environ.get("GRAPH_REAL_CODEX") != "1":
        print("Set GRAPH_REAL_CODEX=1 to run the real Codex proof.", file=sys.stderr)
        return 2

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    evidence_dir = ROOT / "reports" / stamp / "real-codex-replaceable-worker"
    evidence_dir.mkdir(parents=True, exist_ok=True)

    task_id = f"graph-real-codex-proof-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    worktree = create_worktree_via_agent_start(
        project="portfolio-ops", task_id=task_id, dry_run=True
    )
    worktree_path = Path(worktree).resolve()
    if worktree_path == Path("/home/jerry").resolve():
        print("refusing home worktree", file=sys.stderr)
        return 1

    db_path = evidence_dir / "graph-control.sqlite"
    store = SqliteControlPlaneStore(str(db_path))
    rt = DurableGraphRuntime(store)
    harness = GraphHarness(rt)

    base_sha = os.popen(f"git -C {worktree_path} rev-parse HEAD").read().strip()
    branch = os.popen(f"git -C {worktree_path} branch --show-current").read().strip()

    # Extra instruction keeps the live Codex node bounded and cheap.
    extra = (
        "For this proof: do NOT modify product code. Only create "
        ".agent-session/result.json with INVESTIGATION_COMPLETED "
        "(node A) or BUILD_COMPLETED with the current HEAD sha (node B). "
        "Then stop immediately."
    )

    run = rt.create_run(
        objective=(
            "Phase 1B proof: real Codex replaceable worker A then B "
            "without conversation continuity"
        ),
        project="portfolio-ops",
        risk_tier="low",
        success_condition="Two sequential nodes completed by distinct Codex processes",
        base_sha=base_sha,
        worktree=str(worktree_path),
        branch=branch or None,
    )

    timeout = float(os.environ.get("GRAPH_REAL_CODEX_TIMEOUT", "900"))

    # --- Worker A: investigator ---
    worker_a = RealCodexWorkerAdapter(timeout_sec=timeout, ephemeral=True)
    out_a = harness.step(
        run.run_id,
        worker=worker_a,
        model_profile="codex-route",
        extra_context={"extra_instructions": extra},
    )
    pid_a = worker_a.last_launch.pid if worker_a.last_launch else None
    exited_a = wait_pid_exited(pid_a, timeout_sec=60) if pid_a else False

    evidence_a = {
        "run_id": run.run_id,
        "accepted": out_a.apply.accepted,
        "attempt": out_a.attempt.to_dict(),
        "apply": out_a.apply.to_dict(),
        "launch": worker_a.last_launch.to_dict() if worker_a.last_launch else None,
        "pid_exited": exited_a,
        "current_node_after": rt.get_run(run.run_id).current_node,
        "state_version_after": rt.get_run(run.run_id).state_version,
    }
    (evidence_dir / "worker-a.json").write_text(
        json.dumps(evidence_a, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    if not out_a.apply.accepted or not exited_a:
        (evidence_dir / "SUMMARY.md").write_text(
            "# Real Codex proof FAILED at worker A\n\n"
            + json.dumps(evidence_a, indent=2)
            + "\n",
            encoding="utf-8",
        )
        rt.close()
        return 1

    # Close runtime process A ownership; B uses a fresh runtime object.
    rt.close()
    time.sleep(0.5)

    store_b = SqliteControlPlaneStore(str(db_path))
    rt_b = DurableGraphRuntime(store_b)
    harness_b = GraphHarness(rt_b)
    run_mid = rt_b.get_run(run.run_id)
    assert run_mid.current_node == "builder", run_mid.current_node

    # Builder extra: still no product edits; report current HEAD as head_sha.
    extra_b = (
        "For this proof: do NOT modify product code. Read HEAD via git rev-parse. "
        "Write .agent-session/result.json with BUILD_COMPLETED and that head_sha. Stop."
    )
    worker_b = RealCodexWorkerAdapter(timeout_sec=timeout, ephemeral=True)
    out_b = harness_b.step(
        run.run_id,
        worker=worker_b,
        model_profile="codex-route",
        extra_context={"extra_instructions": extra_b},
    )
    pid_b = worker_b.last_launch.pid if worker_b.last_launch else None
    exited_b = wait_pid_exited(pid_b, timeout_sec=60) if pid_b else False

    evidence_b = {
        "run_id": run.run_id,
        "accepted": out_b.apply.accepted,
        "attempt": out_b.attempt.to_dict(),
        "apply": out_b.apply.to_dict(),
        "launch": worker_b.last_launch.to_dict() if worker_b.last_launch else None,
        "pid_exited": exited_b,
        "pid_a": pid_a,
        "pid_b": pid_b,
        "pids_distinct": pid_a != pid_b,
        "current_node_after": rt_b.get_run(run.run_id).current_node,
        "state_version_after": rt_b.get_run(run.run_id).state_version,
        "events": [e.to_dict() for e in rt_b.list_events(run.run_id)],
        "projection_replay_ok": rt_b.verify_projection_matches_events(run.run_id)["equal"],
    }
    (evidence_dir / "worker-b.json").write_text(
        json.dumps(evidence_b, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    ok = (
        out_b.apply.accepted
        and exited_b
        and pid_a != pid_b
        and evidence_b["projection_replay_ok"]
        and worker_a.last_launch is not None
        and worker_b.last_launch is not None
        and "--ephemeral" in worker_a.last_launch.command
        and "--ephemeral" in worker_b.last_launch.command
        and "resume" not in worker_a.last_launch.command
        and "resume" not in worker_b.last_launch.command
    )
    summary = {
        "ok": ok,
        "worktree": str(worktree_path),
        "db": str(db_path),
        "worker_a": evidence_a,
        "worker_b": evidence_b,
        "acceptance": {
            "1_run_attempt": True,
            "2_codex_via_codex_route": bool(
                worker_a.last_launch and "codex-route" in worker_a.last_launch.command[0]
            ),
            "3_bound_worktree_not_home": str(worktree_path) != "/home/jerry",
            "4_context_env": (worktree_path / ".agent-session/worker-context.json").is_file(),
            "5_structured_result": out_a.apply.accepted and out_b.apply.accepted,
            "6_ingest": out_a.apply.accepted and out_b.apply.accepted,
            "7_durable_events": evidence_b["projection_replay_ok"],
            "8_a_exited": exited_a,
            "9_b_continued": out_b.apply.accepted,
            "10_no_shared_thread": bool(
                pid_a != pid_b
                and worker_a.last_launch
                and worker_b.last_launch
                and "--ephemeral" in worker_a.last_launch.command
                and "--ephemeral" in worker_b.last_launch.command
            ),
        },
    }

    (evidence_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (evidence_dir / "SUMMARY.md").write_text(
        "# Real Codex replaceable worker proof\n\n"
        f"- ok: **{ok}**\n"
        f"- worktree: `{worktree_path}`\n"
        f"- run_id: `{run.run_id}`\n"
        f"- pid A / B: `{pid_a}` / `{pid_b}`\n"
        f"- node after B: `{evidence_b['current_node_after']}`\n",
        encoding="utf-8",
    )
    rt_b.close()
    print(json.dumps({"ok": ok, "evidence_dir": str(evidence_dir)}, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
