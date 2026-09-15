#!/usr/bin/env python3
"""Dry-run scenario for Agent Graph Runtime v0.

Does not call Cursor Agents API, GitHub, merge, or deploy.
Prints the full event trace and reduced final state as JSON.
"""

from __future__ import annotations

import json
import sys
from typing import Any

from agent_graph.models import Event
from agent_graph.runtime import GraphRuntime


TASK_ID = "task-dry-run-001"
REPO = "jerry200176-png/portfolio-ops"
BASE = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
HEAD_V1 = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
HEAD_V2 = "cccccccccccccccccccccccccccccccccccccccc"


def _e(
    event_id: str,
    event_type: str,
    node: str,
    actor_id: str,
    actor_role: str,
    *,
    head_sha: str | None = None,
    base_sha: str | None = BASE,
    conclusion: str | None = None,
    evidence: dict[str, Any] | None = None,
    timestamp: str = "2026-07-27T00:00:00Z",
) -> Event:
    return Event(
        event_id=event_id,
        task_id=TASK_ID,
        timestamp=timestamp,
        event_type=event_type,
        node=node,
        actor_id=actor_id,
        actor_role=actor_role,
        repository=REPO,
        base_sha=base_sha,
        head_sha=head_sha,
        conclusion=conclusion,
        evidence=evidence or {},
    )


def run_happy_path() -> dict[str, Any]:
    """
    Scenario:
      1. create task
      2. investigator completes
      3. builder completes
      4. reviewer rejects
      5. builder repairs (new head SHA)
      6. new reviewer approves
      7. human gate
      8. human approves specified head SHA
      9. approved_for_effect (Phase 1C terminal)
    """
    rt = GraphRuntime()
    steps = [
        _e(
            "evt-001",
            "TASK_CREATED",
            "intake",
            "system",
            "system",
            head_sha=BASE,
            conclusion="created",
            evidence={"title": "dry-run graph runtime v0"},
            timestamp="2026-07-27T00:01:00Z",
        ),
        _e(
            "evt-002",
            "INVESTIGATION_COMPLETED",
            "investigator",
            "agent-investigator-1",
            "investigator",
            head_sha=BASE,
            conclusion="investigated",
            evidence={"findings": "root cause identified (synthetic)"},
            timestamp="2026-07-27T00:02:00Z",
        ),
        _e(
            "evt-003",
            "BUILD_COMPLETED",
            "builder",
            "agent-builder-1",
            "builder",
            head_sha=HEAD_V1,
            conclusion="built",
            evidence={"branch": "feat/agent-graph-runtime-v0", "pr": "dry-run"},
            timestamp="2026-07-27T00:03:00Z",
        ),
        _e(
            "evt-004",
            "REVIEW_REJECTED",
            "reviewer",
            "agent-reviewer-1",
            "reviewer",
            head_sha=HEAD_V1,
            conclusion="rejected",
            evidence={"reason": "missing regression test (synthetic)"},
            timestamp="2026-07-27T00:04:00Z",
        ),
        _e(
            "evt-005",
            "BUILD_COMPLETED",
            "builder",
            "agent-builder-1",
            "builder",
            head_sha=HEAD_V2,
            conclusion="built",
            evidence={"fix": "added regression test (synthetic)"},
            timestamp="2026-07-27T00:05:00Z",
        ),
        _e(
            "evt-006",
            "REVIEW_APPROVED",
            "reviewer",
            "agent-reviewer-2",
            "reviewer",
            head_sha=HEAD_V2,
            conclusion="approved",
            evidence={"note": "different reviewer than builder"},
            timestamp="2026-07-27T00:06:00Z",
        ),
        _e(
            "evt-007",
            "HUMAN_APPROVED",
            "human_gate",
            "founder",
            "human",
            head_sha=HEAD_V2,
            conclusion="approved",
            evidence={"approved_head_sha": HEAD_V2},
            timestamp="2026-07-27T00:07:00Z",
        ),
    ]

    results = []
    for event in steps:
        result = rt.apply(event)
        results.append(result.to_dict())
        if not result.accepted:
            break

    final = rt.state_for(TASK_ID)
    return {
        "mode": "dry-run",
        "external_agents_created": 0,
        "credential_exposed": False,
        "cursor_api_called": False,
        "github_operator_called": False,
        "merge_performed": False,
        "deploy_performed": False,
        "task_id": TASK_ID,
        "apply_results": results,
        "event_trace": rt.event_trace(TASK_ID),
        "final_state": final.snapshot(),
    }


def run_stop_path() -> dict[str, Any]:
    """Trigger a persisted stop and verify replay preserves the blocked state."""
    rt = GraphRuntime()
    steps = [
        _e(
            "stop-001",
            "TASK_CREATED",
            "intake",
            "system",
            "system",
            head_sha=BASE,
            conclusion="created",
            timestamp="2026-07-27T00:11:00Z",
        ),
        _e(
            "stop-002",
            "NODE_FAILED",
            "investigator",
            "agent-investigator-1",
            "investigator",
            head_sha=BASE,
            conclusion="error",
            evidence={"failure_signature": "repeatable-investigator-failure"},
            timestamp="2026-07-27T00:12:00Z",
        ),
        _e(
            "stop-003",
            "NODE_FAILED",
            "investigator",
            "agent-investigator-1",
            "investigator",
            head_sha=BASE,
            conclusion="error",
            evidence={"failure_signature": "repeatable-investigator-failure"},
            timestamp="2026-07-27T00:13:00Z",
        ),
    ]

    results = []
    for event in steps:
        result = rt.apply(event)
        results.append(result.to_dict())

    final = rt.state_for(TASK_ID)
    replayed = rt.replay(TASK_ID)
    return {
        "mode": "dry-run",
        "stop_reason": "duplicate failure signature",
        "task_id": TASK_ID,
        "apply_results": results,
        "event_trace": rt.event_trace(TASK_ID),
        "final_state": final.snapshot(),
        "replayed_state": replayed.snapshot(),
    }


def main() -> int:
    out = {
        "happy_path": run_happy_path(),
        "stop_path": run_stop_path(),
    }
    json.dump(out, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    final = out["happy_path"]["final_state"]
    stopped = out["stop_path"]["final_state"]
    ok = (
        final["task_status"] == "approved_for_effect"
        and final["current_node"] == "approved_for_effect"
        and final["human_approved"] is True
        and final["approved_head_sha"] == HEAD_V2
        and final["builder_actor_id"] == "agent-builder-1"
        and final["reviewer_actor_id"] == "agent-reviewer-2"
        and final["builder_actor_id"] != final["reviewer_actor_id"]
        and stopped["task_status"] == "blocked"
        and stopped["stopped"] is True
        and out["stop_path"]["replayed_state"] == stopped
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
