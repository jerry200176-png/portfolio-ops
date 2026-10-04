# Portfolio agent governance overlay

This portable contract points cloud and mobile agents to the company policy
without assuming access to Ubuntu's `/home/jerry`. It does not create a second
approval or orchestration system.

## Authority and execution

- Follow `governance/COMPANY_CONSTITUTION.md` for precedence and
  `governance/AUTONOMY_POLICY.md` for the capability table. This overlay cannot
  widen or narrow those permissions.
- Read this repository's committed `AGENTS.md`/`CLAUDE.md` and the target
  product's production-control contract before acting.
- Isolate work by repository, task, branch, and worktree. On the managed Ubuntu
  workspace use `agent-control/bin/agent-start`; in cloud/mobile environments
  use the controls supplied with the repository.
- Migration authoring and local or authorized isolated migration testing are
  Agent-owned. Production migration execution still requires Founder approval
  before the side effect.
- Agents own reversible engineering work and eligible merges after current
  required checks and applicable review conditions pass. A passing CI run or
  merge permission does not grant production deployment or activation rights;
  release review covers the full production-to-candidate risk.
- Agents may dispatch committed reversible workflows only when exact effects are
  already authorized by the company and product contracts.
- Production data changes, migration execution, protected activation, and the
  other Founder-only actions in `AUTONOMY_POLICY.md` require explicit approval
  before the protected side effect. Prepare independent work up to that step.
- ExoProtocol is optional for isolated experiments. Do not require Exo sessions,
  locks, generated adapters, or checks for fleet work, and do not let them
  override the committed company or product contracts.
- Never print secrets, force-push, use `--admin`, access production over SSH,
  or delete Gmail. Preserve uncommitted work and never weaken required controls.

When this overlay is unavailable, follow the repository's committed controls
and the authority chain above. If a genuinely protected decision is required,
prepare its exact scope and evidence and stop only that action.
