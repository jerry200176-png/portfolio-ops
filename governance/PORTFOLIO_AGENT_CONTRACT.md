# Portfolio agent governance overlay

This file is committed because a cloud or mobile agent may not have access to
Ubuntu's `/home/jerry`. The canonical, detailed policy is maintained in
`jerry200176-png/portfolio-ops` under `governance/`; this file is the portable
minimum that travels with each governed repository.

## Required behavior

- Treat Cursor, Codex, Claude Code, and Cubelv as untrusted writers.
- Before writing, identify the repository, branch/worktree, task scope, risk,
  and verification plan. Never work directly on the default branch.
- Read this repository's committed instructions and ExoProtocol's `.exo/`
  constitution/lock when present. Do not edit governance files to make a task
  pass or to bypass a lock, ticket, session, CI check, or review.
- Migration authoring and local or authorized isolated migration testing are
  Agent-owned engineering work. Production migration execution and production
  deployment/activation require explicit Founder approval before the side
  effect; a merge or workflow that triggers them is part of that boundary.
  Destructive migration design, material schema-contract risk, identity/
  permission/security policy, billing/payment semantics, and material product
  policy remain Founder decisions. Continue separable containment and ask only
  when an unresolved policy blocks the next safe step.
- Every change goes through a pull request. **Required GitHub checks are the
  acceptance.** After they are green, agents squash-merge eligible changes
  only when the merge will not trigger unapproved production activation, per
  `jerry200176-png/portfolio-ops` `governance/AUTONOMY_POLICY.md` and
  `docs/fleet-merge-policy.md`. Founder-risk code may be prepared and reviewed
  as a PR; R3 needs a Repair Manifest where applicable. Branch prefixes never
  grant a bypass of required checks. Do not `--admin` merge.
- The Agent also closes issues (when evidence is filled), sends/replies on
  Gmail for the task, and dispatches only committed reversible,
  non-production workflows. Production side effects still require the Founder
  decision above. Machine bans: secret print, force-push, production SSH,
  Gmail trash/delete.
- Prefer mature open-source tools for generic lint, security, workflow, and
  policy checks; keep company-specific risk, provenance, evidence, and release
  boundaries in committed policy and CI.

If a product overlay bans Pi tests, campus leaks, or adds required CI, those
stricter **safety** rules win. A product overlay must **not** add a Founder
rubber-stamp; portfolio-ops owns the operator table.
