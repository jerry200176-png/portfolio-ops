"""Policy-based human_gate advance (non-Founder tiers).

When risk policy does not require Founder Approval, the control plane may
advance human_gate via agent-operator — not by forging Founder credentials.
"""

from __future__ import annotations

from typing import Any

from .durable_runtime import DurableGraphRuntime
from .risk_policy import requires_founder_approval


def advance_human_gate_by_policy(
    runtime: DurableGraphRuntime,
    run_id: str,
    *,
    action: str = "merge",
) -> dict[str, Any]:
    """Advance waiting_for_approval when Founder gate is not required by policy."""
    run = runtime.get_run(run_id)
    if run.current_node != "human_gate" and run.status != "waiting_for_approval":
        return {
            "accepted": False,
            "reason": (
                f"run {run_id} not at human_gate "
                f"(node={run.current_node} status={run.status})"
            ),
            "run": run.to_dict(),
        }
    if requires_founder_approval(run.risk_tier):
        return {
            "accepted": False,
            "reason": "Founder approval required for this risk tier",
            "blocker": "founder_approval_required",
            "run": run.to_dict(),
        }
    if not run.head_sha:
        return {
            "accepted": False,
            "reason": "run has no head_sha to bind approval",
            "blocker": "missing_head_sha",
            "run": run.to_dict(),
        }
    return runtime.grant_founder_approval(
        run_id=run_id,
        action=action,
        head_sha=run.head_sha,
        actor="agent-operator",
    )
