# Company workspace agent entry point

Before changing any repository, read:

1. `/home/jerry/workspace/portfolio-ops/CLAUDE.md` and `AGENTS.md`
2. `/home/jerry/workspace/portfolio-ops/governance/company-agent-contract.yaml`
3. `/home/jerry/workspace/portfolio-ops/docs/agent-operating-loop.md`
4. `/home/jerry/workspace/portfolio-ops/workspace.manifest.yaml`
5. the target repository's own instructions

Use `/home/jerry/workspace/agent-control/bin/agent-start` for isolated task
worktrees. Follow discover -> research -> plan -> implement -> verify -> review
-> learn. Eligible T0/T1 work uses the inner loop in
`docs/verify-retry-loop.md`. If the same step fails twice or a gate is stuck
for five minutes, record the blocker and stop retrying silently. On 收工,
follow `docs/session-closeout.md`. Record plans and evidence in GitHub and in
the control plane. After required GitHub checks, the Agent operates within
`docs/fleet-merge-policy.md`; machine bans and product-specific protected
boundaries remain in force.
