# Cross-agent governance bootstrap

**Version:** 1.1.0
**Canonical owner:** Portfolio Ops (`jerry200176-png/portfolio-ops`)

This is the small, portable contract that every local or cloud agent should
load before it changes a governed repository. The detailed policy remains in
`governance/COMPANY_CONSTITUTION.md`, `governance/AUTONOMY_POLICY.md`, and the
target product repository's own `AGENTS.md`/`CLAUDE.md`.

## Required bootstrap

1. Identify the execution environment, repository root, branch/worktree, task
   scope, risk tier, and verification plan before writing.
2. Use the target repository's committed instructions and production control
   contract as the source of truth. Do not replace them with chat memory,
   local assumptions, or a second hand-written policy.
3. On Ubuntu, the **canonical session path** is
   `/home/jerry/workspace/agent-control/bin/agent-start` (also installed as
   `~/.local/bin/agent-start`). It creates the approved task worktree,
   preflight, and manifest. Do not edit legacy checkouts:
   `/home/jerry/alltrue`, `/home/jerry/workspace/AllTrue_System`,
   `/home/jerry/workspace/AllTrue_System-clean`.
4. In cloud/mobile-started work, assume `/home/jerry` and local credentials do
   not exist. Use only the repository and environment supplied to the task;
   if this contract or a required policy file is unavailable, stop and report
   the missing context instead of inventing a replacement.
5. Prefer mature, maintained open-source tools for generic checks. Keep custom
   governance only for company-specific risk, evidence, provenance, approval,
   and deployment boundaries.
6. Never claim a change is complete without the relevant diff, test/CI result,
   and (for release work) deployment and smoke evidence. The implementing
   Agent is the operator (`governance/AUTONOMY_POLICY.md`) for reversible
   engineering work: investigate, plan, change application code, author
   migrations, test locally or in authorized isolated environments, and
   prepare PRs without implementation-detail approval. Merge only when
   required checks pass and any triggered release is authorized for the full
   production-to-candidate difference. Production migration execution and
   product-defined protected activation require Founder approval before the side effect; a
   destructive design that locks in product direction requires a decision
   before implementation commits to it. If a repair exposes a material
   product-policy question, continue separable containment and ask only when
   that decision blocks the next safe step; do not invent product semantics.
   Machine bans remain: secrets, force-push, `--admin`, production SSH, Gmail
   delete.

## Enforcement boundary

This file gives agents shared context; it is not a security sandbox. Local
preflight/hooks and remote CI/GitHub rulesets are the enforcement layers. A
local agent must not weaken those controls to make a task pass.

## Session kernel (canonical vs experiment)

- **Canonical:** `agent-control` (Phase 0.5). One task → one branch → one
  isolated worktree under `/home/jerry/workspace/tasks/<project>/` with a
  session manifest and provenance.
- **Experiment only:** ExoProtocol. Do **not** require Exo CI or Exo ruleset
  checks. Do **not** treat Exo-generated adapter blocks as a second policy
  source over product `AGENTS.md`/`CLAUDE.md`. Keep any `.exo/` trees local to
  experiment sessions; do not expand Exo into a fleet framework.

## Open-source baseline

- **Policy-as-code (optional later):** OPA/Conftest for fleet metadata only —
  not product runtime contracts.
- **Generic checks:** pre-commit, commitlint, actionlint, zizmor, gitleaks,
  OpenSSF Scorecard, and GitHub Rulesets where each tool owns the problem.

Cursor, Codex, Claude Code, and Cubelv are untrusted writers. Cubelv PRs are
governed entirely by committed repository checks, provenance, and GitHub
Rulesets.
