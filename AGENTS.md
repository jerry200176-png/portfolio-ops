# Agent entry point

This file exists for non-Claude-Code automation that reads `AGENTS.md` by
convention. The authoritative operating rules live in `CLAUDE.md` at the root
of this repository, with procedure in
`.claude/skills/portfolio-maintain/SKILL.md`. Read both before acting.

All local and cloud agents should also load `governance/AGENT_BOOTSTRAP.md`.
It is the compact cross-agent contract; the detailed authority remains in
`governance/` and this repository's `CLAUDE.md`.

Do not duplicate rules here — if this file and `CLAUDE.md` ever disagree,
`CLAUDE.md` wins.
Company-wide contract: read `governance/company-agent-contract.yaml` and
`docs/agent-operating-loop.md` before acting on a portfolio task.

## Company authority and session gateway

Read `governance/AGENT_BOOTSTRAP.md` before governed work. The instruction
precedence is in `governance/COMPANY_CONSTITUTION.md`; execution permissions
are in `governance/AUTONOMY_POLICY.md`. The portable minimum for cloud and
mobile agents is `governance/PORTFOLIO_AGENT_CONTRACT.md`.

On the managed Ubuntu workspace, use `agent-control/bin/agent-start` for an
isolated task worktree, preflight, and provenance. In cloud or mobile work,
use the supplied repository and its committed controls; do not assume the
local gateway or `/home/jerry` exists.

ExoProtocol is optional for isolated experiments. Its sessions, locks,
generated adapters, and CI are not required for fleet work and cannot override
these committed contracts. Existing product, data, security, and protected
production-action boundaries remain in force.

## Portfolio governance overlay

Read `governance/PORTFOLIO_AGENT_CONTRACT.md` before writing. It is committed
for cloud/mobile agents and contains the company's PR, approval, production,
and Founder-approval boundaries.
