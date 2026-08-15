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
- Every change goes through a pull request. **Required GitHub checks are the
  acceptance.** After they are green, agents squash-merge R0–R3 per
  `jerry200176-png/portfolio-ops` `governance/AUTONOMY_POLICY.md` and
  `docs/fleet-merge-policy.md`. R3 needs a Repair Manifest in the PR. Branch
  prefixes never grant a bypass of required checks. Do not `--admin` merge.
- The Agent also closes issues (when evidence is filled), sends/replies on
  Gmail for the task, and dispatches committed product workflows. Machine
  bans: secret print, force-push, production SSH, Gmail trash/delete.
- Prefer mature open-source tools for generic lint, security, workflow, and
  policy checks; keep company-specific risk, provenance, evidence, and release
  boundaries in committed policy and CI.

If a product overlay bans Pi tests, campus leaks, or adds required CI, those
stricter **safety** rules win. A product overlay must **not** add a Founder
rubber-stamp; portfolio-ops owns the operator table.
