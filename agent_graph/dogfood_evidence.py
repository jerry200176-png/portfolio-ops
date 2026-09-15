"""Assemble machine-readable Part A dogfood evidence from canonical state."""

from __future__ import annotations

import json
import subprocess
from typing import Any, Optional


def _git(worktree: Optional[str], *args: str) -> Optional[str]:
    if not worktree:
        return None
    try:
        return subprocess.check_output(
            ["git", "-C", worktree, *args],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return None


def collect_dogfood_evidence(
    *,
    runtime: Any,
    store: Any,
    run_id: str,
    scheduler_id: Optional[str] = None,
    mode: str = "schedule-run",
) -> dict[str, Any]:
    """Build the required Part A evidence object (machine-readable)."""
    run = runtime.get_run(run_id)
    events = [e.to_dict() for e in runtime.list_events(run_id)]
    attempt_cols = {
        r[1] for r in store._conn.execute("PRAGMA table_info(attempts)").fetchall()
    }
    wanted = [
        "attempt_id",
        "node",
        "worker_type",
        "worker_pid",
        "worker_pgid",
        "status",
        "fencing_token",
        "started_at",
        "ended_at",
        "finished_at",
    ]
    select = ", ".join(c for c in wanted if c in attempt_cols)
    attempts_rows = store._conn.execute(
        f"SELECT {select} FROM attempts WHERE run_id=? ORDER BY started_at",
        (run_id,),
    ).fetchall()
    attempts = [dict(r) for r in attempts_rows]

    effects = [e.to_dict() for e in store.list_effects(run_id)]
    approvals = [a.to_dict() for a in store.list_approvals(run_id)]

    node_transitions: list[dict[str, Any]] = []
    for ev in events:
        et = ev.get("event_type") or ev.get("type")
        if isinstance(et, str) and (
            "NODE" in et or "STATUS" in et or et in ("TASK_CREATED", "HUMAN_APPROVED")
        ):
            node_transitions.append(
                {
                    "at": ev.get("created_at") or ev.get("at"),
                    "event_type": et,
                    "payload": ev.get("payload") or ev.get("evidence"),
                }
            )

    obs = (run.graph_snapshot or {}).get("observations") or {}
    ci_by_sha = obs.get("ci_by_sha") or {}
    pr_facts = [
        f
        for f in (obs.get("facts") or [])
        if f.get("fact_type")
        in ("PR_EXISTS", "PR_MERGED", "CI_GREEN", "CI_PENDING", "CI_FAILED")
    ]

    changed_files: list[str] = []
    if run.worktree and run.base_sha and run.head_sha and run.base_sha != run.head_sha:
        diff = _git(run.worktree, "diff", "--name-only", f"{run.base_sha}..{run.head_sha}")
        if diff:
            changed_files = [ln for ln in diff.splitlines() if ln.strip()]

    merge_effects = [e for e in effects if e.get("action") == "github_pr_merge"]
    create_effects = [e for e in effects if e.get("action") == "github_pr_create"]
    merge_sha = None
    pr_number = None
    pr_url = None
    for e in create_effects + merge_effects:
        try:
            raw = e.get("result_json")
            if raw:
                data = json.loads(raw) if isinstance(raw, str) else raw
                pr_number = pr_number or data.get("number")
                pr_url = pr_url or data.get("url")
                merge_sha = merge_sha or data.get("mergeCommitOid") or data.get("sha")
        except (TypeError, ValueError, json.JSONDecodeError):
            pass
        if e.get("external_ref") and not pr_url:
            pr_url = e.get("external_ref")

    head = run.head_sha or ""
    return {
        "schema": "graph-control-plane.dogfood-evidence.v1",
        "mode": mode,
        "scheduler_id": scheduler_id,
        "run_id": run_id,
        "goal_id": run.goal_id,
        "attempt_ids": [a["attempt_id"] for a in attempts],
        "worker_identities": [
            {
                "attempt_id": a["attempt_id"],
                "node": a["node"],
                "worker_type": a.get("worker_type"),
                "worker_pid": a.get("worker_pid"),
                "worker_pgid": a.get("worker_pgid"),
                "fencing_token": a.get("fencing_token"),
                "status": a.get("status"),
            }
            for a in attempts
        ],
        "node_transitions": node_transitions
        or [{"current_node": run.current_node, "status": run.status}],
        "changed_files": changed_files,
        "test_evidence": {
            "ci_by_sha": ci_by_sha,
            "head_sha_ci": ci_by_sha.get(head),
            "observation_facts": pr_facts,
        },
        "pr": {"number": pr_number, "url": pr_url},
        "exact_head_sha": head,
        "ci_state": ci_by_sha.get(head),
        "approvals": approvals,
        "effect_ids": [e.get("effect_id") for e in effects],
        "effects": effects,
        "merge_sha": merge_sha,
        "terminal_reconciliation": {
            "status": run.status,
            "current_node": run.current_node,
            "closed": run.closed,
            "stopped": run.stopped,
            "blocker": run.blocker,
            "closed_success": run.status == "closed_success" and bool(run.closed),
        },
        "implementation_workers_are_codex": all(
            a.get("worker_type") == "codex"
            for a in attempts
            if a.get("node") in ("investigator", "builder")
        ),
    }
