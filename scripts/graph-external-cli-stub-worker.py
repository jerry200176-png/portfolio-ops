#!/usr/bin/env python3
"""Deterministic external CLI stub worker (independent process).

Reads worker-invocation.json / env, writes .agent-session/result.json.
Does not touch the control-plane database. Used to prove disposable
process handoff without depending on Cursor/Codex availability.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path


OUTCOME_BY_NODE = {
    "investigator": ("INVESTIGATION_COMPLETED", "investigator", "inv-stub"),
    "builder": ("BUILD_COMPLETED", "builder", "builder-stub"),
    "reviewer": ("REVIEW_APPROVED", "reviewer", "reviewer-stub"),
}


def main() -> int:
    parser = argparse.ArgumentParser(description="graph external_cli stub worker")
    parser.add_argument("--worktree", required=True)
    parser.add_argument("--sleep-sec", type=float, default=0.0)
    parser.add_argument("--crash-before-result", action="store_true")
    parser.add_argument("--head-sha", default="")
    args = parser.parse_args()

    worktree = Path(args.worktree).resolve()
    session = worktree / ".agent-session"
    session.mkdir(parents=True, exist_ok=True)

    invocation_path = Path(
        os.environ.get("WORKER_INVOCATION_PATH") or (session / "worker-invocation.json")
    )
    result_path = Path(os.environ.get("WORKER_RESULT_PATH") or (session / "result.json"))

    invocation: dict = {}
    if invocation_path.is_file():
        invocation = json.loads(invocation_path.read_text(encoding="utf-8"))

    work_ref = invocation.get("work_ref") or {}
    exec_id = invocation.get("execution_identity") or {}
    run_id = str(os.environ.get("RUN_ID") or work_ref.get("run_id") or "")
    attempt_id = str(os.environ.get("ATTEMPT_ID") or work_ref.get("attempt_id") or "")
    node = str(os.environ.get("NODE") or work_ref.get("node") or "investigator")
    expected_sv = exec_id.get("expected_state_version")
    if expected_sv is None:
        expected_sv = os.environ.get("EXPECTED_STATE_VERSION")

    if args.sleep_sec > 0:
        time.sleep(float(args.sleep_sec))
    if args.crash_before_result:
        # Exit without writing result — simulates worker death.
        return 137

    if node not in OUTCOME_BY_NODE:
        payload = {
            "schema_version": "1.0",
            "status": "failure",
            "summary": f"stub has no fixture for node={node}",
            "idempotency_key": f"{attempt_id}:NODE_UNSUPPORTED",
            "artifacts": [],
            "evidence": [{"kind": "stub", "ref": attempt_id, "summary": "unsupported_node"}],
            "proposed_outcome": None,
            "run_id": run_id,
            "attempt_id": attempt_id,
            "node": node,
            "expected_state_version": expected_sv,
        }
        result_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return 1

    outcome_type, actor_role, actor_id = OUTCOME_BY_NODE[node]
    head = args.head_sha or os.environ.get("HEAD_SHA") or ("b" * 40)
    base = os.environ.get("BASE_SHA") or ("a" * 40)
    payload = {
        "schema_version": "1.0",
        "status": "success",
        "summary": f"stub completed {outcome_type} via independent CLI process",
        "idempotency_key": f"{attempt_id}:{outcome_type}",
        "artifacts": [{"kind": "note", "uri": f"stub://{attempt_id}"}],
        "evidence": [
            {
                "kind": "stub",
                "ref": attempt_id,
                "summary": "external_cli_stub",
                "pid": os.getpid(),
            }
        ],
        "proposed_outcome": {
            "outcome_type": outcome_type,
            "actor_id": actor_id,
            "actor_role": actor_role,
            "head_sha": head if node == "builder" else head,
            "base_sha": base,
            "conclusion": "ok",
            "evidence": {"source": "external_cli_stub"},
            "repository": f"jerry200176-png/{os.environ.get('PROJECT', 'portfolio-ops')}",
        },
        "run_id": run_id,
        "attempt_id": attempt_id,
        "node": node,
        "expected_state_version": expected_sv,
    }
    result_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
