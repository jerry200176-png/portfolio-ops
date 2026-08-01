# Contributing to Portfolio Ops

Portfolio Ops is a governance and evidence repository, not a product-code
monorepo. Keep one change series focused on one concern and record the
evidence and verification commands in the pull request.

## Required workflow

1. Start from the current default branch and use a dedicated branch.
2. Keep product changes in the product repository and worktree that owns them.
3. Do not delete, move, reset, clean, merge, rebase, or force-push without the
   explicit Founder approval required by `CLAUDE.md`.
4. Run the relevant tests and `git diff --check` before requesting review.
5. Use Draft PRs until scope, evidence, rollback, and remaining uncertainty are
   clear.

## Pull requests

Every PR should state: problem, scope, evidence, tests run, risk, rollback,
and what remains unverified. Governance changes must also explain which
workspace paths they affect and which paths they deliberately leave untouched.
