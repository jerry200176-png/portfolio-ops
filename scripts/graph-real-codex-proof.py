#!/usr/bin/env python3
"""Real Codex A→B replaceability + death-before-result proofs (integration gate).

Requires GRAPH_REAL_CODEX=1. Canonical SQLite is stored outside the worker worktree.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from agent_graph.canonical_paths import (
    assert_canonical_db_outside_worktree,
    ensure_canonical_db_parent,
)
from agent_graph.durable_runtime import DurableGraphRuntime
from agent_graph.harness import GraphHarness
from agent_graph.real_codex_adapter import RealCodexWorkerAdapter, wait_pid_exited
from agent_graph.sqlite_store import SqliteControlPlaneStore
from agent_graph.worktree_bind import create_worktree_via_agent_start


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def main() -> int:
    if os.environ.get("GRAPH_REAL_CODEX") != "1":
        print("Set GRAPH_REAL_CODEX=1 to run the real Codex proof.", file=sys.stderr)
        return 2

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    evidence_dir = ROOT / "reports" / stamp / "real-codex-replaceable-worker"
    evidence_dir.mkdir(parents=True, exist_ok=True)

    # Canonical DB outside any task worktree (and outside this repo checkout when possible).
    db_path = ensure_canonical_db_parent(
        Path("/home/jerry/workspace/state/portfolio-ops/graph-control-phase1b-proof.sqlite")
    )
    if db_path.exists():
        db_path.unlink()

    task_id = f"graph-real-codex-proof-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    worktree = create_worktree_via_agent_start(
        project="portfolio-ops", task_id=task_id, dry_run=True
    )
    worktree_path = Path(worktree).resolve()
    assert_canonical_db_outside_worktree(db_path, worktree_path)

    store = SqliteControlPlaneStore(str(db_path))
    rt = DurableGraphRuntime(store)
    harness = GraphHarness(rt)

    base_sha = os.popen(f"git -C {worktree_path} rev-parse HEAD").read().strip()
    branch = os.popen(f"git -C {worktree_path} branch --show-current").read().strip()
    timeout = float(os.environ.get("GRAPH_REAL_CODEX_TIMEOUT", "900"))

    extra = (
        "For this proof: do NOT modify product code. Only create "
        ".agent-session/result.json with INVESTIGATION_COMPLETED "
        "(node A) or BUILD_COMPLETED with the current HEAD sha (node B). "
        "Then stop immediately. Do not resume any prior session."
    )

    run = rt.create_run(
        objective=(
            "Phase 1B harden proof: real Codex replaceable worker A then B "
            "with canonical DB outside worktree"
        ),
        project="portfolio-ops",
        risk_tier="low",
        success_condition="Two sequential nodes completed by distinct Codex processes",
        base_sha=base_sha,
        worktree=str(worktree_path),
        branch=branch or None,
    )

    db_sha_before_a = _sha256(db_path) if db_path.exists() else None

    # --- Boundary probe: ask Codex to mutate canonical DB path (must fail / no effect) ---
    probe = RealCodexWorkerAdapter(
        timeout_sec=min(timeout, 300),
        ephemeral=True,
        canonical_db_path=db_path,
    )
    # Use a dedicated throwaway attempt via step with instructions to touch DB.
    # We do NOT want this to complete the node successfully.
    probe_extra = (
        f"Attempt to overwrite or append to this absolute path using shell: `{db_path}`. "
        "If the write is denied by sandbox, stop and write result.json with status=failure "
        "summary=sandbox_denied. Do not modify product code."
    )
    # Snapshot events before probe — probe may fail Attempt without transition.
    events_before_probe = len(rt.list_events(run.run_id))
    node_before_probe = rt.get_run(run.run_id).current_node
    out_probe = harness.step(
        run.run_id,
        worker=probe,
        model_profile="codex-route",
        extra_context={"extra_instructions": probe_extra},
    )
    db_sha_after_probe = _sha256(db_path)
    # Run projection node must remain investigator if probe failed without transition.
    # If model somehow succeeded investigation, that's still ok for DB integrity check.
    boundary = {
        "db_path": str(db_path),
        "worktree": str(worktree_path),
        "db_outside_worktree": True,
        "probe_accepted": out_probe.apply.accepted,
        "probe_pid": probe.last_launch.pid if probe.last_launch else None,
        "probe_exited": wait_pid_exited(probe.last_launch.pid, timeout_sec=60)
        if probe.last_launch and probe.last_launch.pid
        else False,
        "db_sha_after_probe": db_sha_after_probe,
        "events_before_probe": events_before_probe,
        "events_after_probe": len(rt.list_events(run.run_id)),
        "node_before_probe": node_before_probe,
        "node_after_probe": rt.get_run(run.run_id).current_node,
        "sandbox": "workspace-write",
    }
    (evidence_dir / "canonical-boundary.json").write_text(
        json.dumps(boundary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    # Reset to a clean Run for A→B if probe advanced the graph unexpectedly.
    if rt.get_run(run.run_id).current_node != "investigator":
        run = rt.create_run(
            objective="Phase 1B harden proof A→B after boundary probe",
            project="portfolio-ops",
            risk_tier="low",
            success_condition="A then B",
            base_sha=base_sha,
            worktree=str(worktree_path),
            branch=branch or None,
        )

    # --- Worker A ---
    worker_a = RealCodexWorkerAdapter(
        timeout_sec=timeout, ephemeral=True, canonical_db_path=db_path
    )
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
        "fencing_token": out_a.attempt.fencing_token,
    }
    (evidence_dir / "worker-a.json").write_text(
        json.dumps(evidence_a, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    if not out_a.apply.accepted or not exited_a:
        (evidence_dir / "SUMMARY.md").write_text(
            "# FAILED at worker A\n" + json.dumps(evidence_a, indent=2), encoding="utf-8"
        )
        rt.close()
        return 1

    rt.close()
    time.sleep(0.3)

    store_b = SqliteControlPlaneStore(str(db_path))
    rt_b = DurableGraphRuntime(store_b)
    harness_b = GraphHarness(rt_b)
    assert rt_b.get_run(run.run_id).current_node == "builder"

    extra_b = (
        "For this proof: do NOT modify product code. Read HEAD via git rev-parse. "
        "Write .agent-session/result.json with BUILD_COMPLETED and that head_sha. Stop."
    )
    worker_b = RealCodexWorkerAdapter(
        timeout_sec=timeout, ephemeral=True, canonical_db_path=db_path
    )
    out_b = harness_b.step(
        run.run_id,
        worker=worker_b,
        model_profile="codex-route",
        extra_context={"extra_instructions": extra_b},
    )
    pid_b = worker_b.last_launch.pid if worker_b.last_launch else None
    exited_b = wait_pid_exited(pid_b, timeout_sec=60) if pid_b else False
    evidence_b = {
        "accepted": out_b.apply.accepted,
        "attempt": out_b.attempt.to_dict(),
        "apply": out_b.apply.to_dict(),
        "launch": worker_b.last_launch.to_dict() if worker_b.last_launch else None,
        "pid_exited": exited_b,
        "pid_a": pid_a,
        "pid_b": pid_b,
        "current_node_after": rt_b.get_run(run.run_id).current_node,
        "events": [e.to_dict() for e in rt_b.list_events(run.run_id)],
        "projection_replay_ok": rt_b.verify_projection_matches_events(run.run_id)["equal"],
    }
    (evidence_dir / "worker-b.json").write_text(
        json.dumps(evidence_b, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    # --- Death before result ---
    death_run = rt_b.create_run(
        objective="death-before-result proof",
        project="portfolio-ops",
        risk_tier="low",
        success_condition="Attempt fails without transition",
        base_sha=base_sha,
        worktree=str(worktree_path),
        branch=branch or None,
    )
    node_before = rt_b.get_run(death_run.run_id).current_node
    ver_before = rt_b.get_run(death_run.run_id).state_version
    killer = RealCodexWorkerAdapter(
        timeout_sec=0.5,
        terminate_grace_sec=2.0,
        ephemeral=True,
        canonical_db_path=db_path,
        # Force hang via a local sleep stub? Prefer real codex with tiny timeout.
        # Using real route but timeout 0.5s → TERM/KILL own group.
    )
    # Use a stub that sleeps so we don't burn Codex tokens and still prove reaping.
    stub = evidence_dir / "sleep-route.sh"
    stub.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        "for a in \"$@\"; do [[ \"$a\" == --dry-run ]] && "
        "echo '{\"profile\":\"terra\",\"model\":\"stub\",\"reasoning_effort_override\":null,"
        "\"reason\":\"t\",\"resolution\":\"selected\",\"requested_tier\":\"terra\","
        "\"selected_tier\":\"terra\"}' && exit 0; done\n"
        "sleep 60 &\n"
        "sleep 60\n",
        encoding="utf-8",
    )
    stub.chmod(0o755)
    killer = RealCodexWorkerAdapter(
        codex_route=str(stub),
        timeout_sec=0.4,
        terminate_grace_sec=1.0,
        ephemeral=True,
        canonical_db_path=db_path,
    )
    out_death = harness_b.step(death_run.run_id, worker=killer)
    death_pid = killer.last_launch.pid if killer.last_launch else None
    death_exited = wait_pid_exited(death_pid, timeout_sec=30) if death_pid else False
    evidence_death = {
        "accepted": out_death.apply.accepted,
        "timed_out": bool(killer.last_launch and killer.last_launch.timed_out),
        "pid": death_pid,
        "pid_exited": death_exited,
        "node_before": node_before,
        "node_after": rt_b.get_run(death_run.run_id).current_node,
        "state_version_before": ver_before,
        "state_version_after": rt_b.get_run(death_run.run_id).state_version,
        "attempt_status": out_death.attempt.status,
        "event_types": [e.type for e in rt_b.list_events(death_run.run_id)],
    }
    (evidence_dir / "death-before-result.json").write_text(
        json.dumps(evidence_death, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    ok = (
        out_b.apply.accepted
        and exited_a
        and exited_b
        and pid_a != pid_b
        and evidence_b["projection_replay_ok"]
        and not out_death.apply.accepted
        and evidence_death["node_after"] == "investigator"
        and evidence_death["state_version_after"] == ver_before
        and death_exited
        and worker_a.last_launch
        and worker_b.last_launch
        and "--ephemeral" in worker_a.last_launch.command
        and "--ephemeral" in worker_b.last_launch.command
    )
    summary = {
        "ok": ok,
        "db_path": str(db_path),
        "worktree": str(worktree_path),
        "boundary": boundary,
        "worker_a": evidence_a,
        "worker_b": evidence_b,
        "death_before_result": evidence_death,
    }
    (evidence_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (evidence_dir / "SUMMARY.md").write_text(
        f"# Real Codex Phase 1B harden proof\n\n"
        f"- ok: **{ok}**\n"
        f"- db: `{db_path}` (outside worktree)\n"
        f"- worktree: `{worktree_path}`\n"
        f"- A/B pids: `{pid_a}` / `{pid_b}`\n"
        f"- death-before-result preserved investigator: "
        f"**{evidence_death['node_after'] == 'investigator'}**\n",
        encoding="utf-8",
    )
    rt_b.close()
    print(json.dumps({"ok": ok, "evidence_dir": str(evidence_dir)}, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
