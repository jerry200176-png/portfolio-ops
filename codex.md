# Portfolio agent governance overlay

This file is committed because a cloud or mobile agent may not have access to
Ubuntu's `/home/jerry`. The canonical, detailed policy is maintained in
`jerry200176-png/portfolio-ops` under `governance/`; this file is the portable
minimum that travels with each governed repository.

## Required behavior

- Before writing, identify the repository, branch/worktree, task scope, risk,
  and verification plan. Never work directly on the default branch.
- Read the committed company authority, this repository's instructions, and
  the target product's production-control contract. Company permission comes
  from `governance/AUTONOMY_POLICY.md`; product rules may retain stricter
  protected-action boundaries.
- Follow required checks, review conditions, evidence, and rollback rules.
  Eligible reversible merges are Agent-owned when those conditions pass;
  merge permission does not grant production deployment or activation rights.
- Prefer maintained tools for generic checks; keep company risk, evidence, and
  release boundaries in the committed authority chain and platform controls.

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
for cloud/mobile agents and summarizes the authority chain and protected
production-action boundaries.
