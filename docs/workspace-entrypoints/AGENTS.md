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
`docs/verify-retry-loop.md`. After required GitHub checks, squash-merge
R0–R2 (`docs/fleet-merge-policy.md`). Record plans and evidence in GitHub and in the control plane. This is
a single-owner company: no second human reviewer is required. Founder-only
R3, extra deploy, deletion, credential, and history-rewrite boundaries stay
explicit.
