# Governance implementation report — 2026-08-01

## Scope

This report records the local implementation pass for the company workspace
governance baseline. No repository was reset, cleaned, merged, rebased,
pruned, moved, removed, deployed, or changed through production controls.

## Implemented

- Added `workspace.manifest.yaml` inventory policy and expanded known legacy and
  active worktree entries.
- Added machine validation for the workspace manifest, portfolio freshness,
  component catalog, and declarative GitHub enforcement policy.
- Added three Backstage-compatible component records under `catalog/`.
- Added read-only workspace discovery and GitHub enforcement audit scripts.
- Added CI validation, pinned action references, Harden Runner audit mode,
  Gitleaks, CodeQL, and OpenSSF Scorecard.
- Added evidence TTL fields: `last_verified_at`, `source_commit`, and
  `evidence_expires_at`.
- Made governance tests explicitly read UTF-8 so they work consistently across
  Windows/WSL and Linux runners.

## Current inventory observation

The read-only inventory scan found 58 Git candidates: 38 clean, 12 dirty, and
8 unresolved/unreadable worktree references. Two new isolated worktrees were
then created for the reviewed product contract PRs. These are findings and
review branches only; no lifecycle action was taken against existing trees.

## Verification

- `python scripts/validate-governance-contract.py`: PASS
- `python -m unittest discover -s tests -v`: PASS — 23 tests
- `bash -n scripts/*.sh`: PASS
- `git diff --check`: PASS
- `scripts/workspace-inventory.sh`: PASS
- `scripts/github-governance-audit.sh`: PASS; audit output kept outside the
  repository under `/tmp`.
- Draft governance PR #17 is pushed and remote Governance CI and Security
  baseline both pass: https://github.com/jerry200176-png/portfolio-ops/pull/17
- GitHub enforcement applied: AllTrue ruleset, Sunrise `main` protection, and
  Portfolio Ops `main` ruleset now require one approval, CODEOWNER review,
  conversation resolution, and required checks with no bypass actors.
- Product component contract PRs opened for review:
  - https://github.com/jerry200176-png/AllTrue_System/pull/1573
  - https://github.com/jerry200176-png/sunrise-cafe/pull/265

## Remaining decisions

- Decide how to resolve the eight unreadable/prunable worktree references.
- Review and merge the three draft PRs when Founder approval is given; no PR
  was merged automatically.
- Enable repository code-scanning upload when the private Portfolio Ops repo
  has the required GitHub Advanced Security capability. Until then, PR CodeQL
  runs analysis with `upload: never`, while Gitleaks and Scorecard gates pass.
