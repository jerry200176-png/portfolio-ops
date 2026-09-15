"""Risk-tier mapping for Founder Approval (Phase 1C).

Canonical sources (do not invent a second ladder):
- docs/fleet-merge-policy.md — R0–R3; R3/Founder-risk requires Founder
- governance/AUTONOMY_POLICY.md — capability table
- governance/company-agent-contract.yaml — irreversible_actions.founder_approval_required
- docs/verify-retry-loop.md — T0/T1 inner-loop eligibility (not merge Founder gate)

Graph `risk_tier` accepts legacy values (low/high) plus R*/T* labels.
Only Founder-risk tiers require durable Founder Approval at human_gate.
"""

from __future__ import annotations

FOUNDER_REQUIRED_TIERS = frozenset(
    {
        "r3",
        "t3",
        "founder",
        "founder-risk",
        "founder_risk",
        "high",
    }
)


def normalize_risk_tier(risk_tier: str | None) -> str:
    return (risk_tier or "low").strip().lower()


def requires_founder_approval(risk_tier: str | None) -> bool:
    """True when durable Founder Approval is mandatory at human_gate."""
    return normalize_risk_tier(risk_tier) in FOUNDER_REQUIRED_TIERS
