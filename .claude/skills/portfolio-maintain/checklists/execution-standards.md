# Execution standards

Applies whenever `execute` mode does real work, via `repo-maintainer`.

## Order

Tier 0 first, then Tier 1, then Tier 2. One repo, one branch/worktree, per
`repo-maintainer` invocation.

## Every unit of work needs

- evidence and root cause (`../../../../docs/evidence-policy.md`)
- success criteria defined before starting, as commands when the work is
  eligible for `docs/verify-retry-loop.md`
- stall escalation: same step failed twice, or five minutes stuck, then ask
- the minimal necessary change — no drive-by refactors
- regression tests, lint, typecheck, static analysis, test, build — actually
  run in this session
- a rollback plan
- a production verification plan (read-only checks the Founder or a
  follow-up session can run post-merge)

## Finish state

- Commit, push the branch, open a PR using
  `../../../../docs/templates/draft-pr-description.md` with `Risk-Class`.
- After required GitHub checks are green, squash-merge R0–R2
  (`docs/fleet-merge-policy.md`). Never `--admin`. Never extra-deploy.
- If CI cannot run: say so plainly in the PR, do not merge, and
  propose the smallest unblock step.

## First-round scope

Do: production reliability, real bugs, data/state inconsistency, CI/deploy
blockers, core UX friction.

Don't (first round): full-repo reformatting, pure renames, large rewrites,
blanket dependency upgrades, large file-moves, documentation-only polish.
See `../../../../docs/prioritization.md`.

## Handoff to review

After a Draft PR is opened, hand off to `evidence-verifier` (and
`security-reviewer`/`ux-reviewer` as relevant) to independently re-derive
the claims — they do not simply restate the implementer's PR description as
fact (`../../../../docs/security-boundaries.md`, reviewer/implementer
isolation).
