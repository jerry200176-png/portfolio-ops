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
8 unresolved/unreadable worktree references. These are findings only; no
lifecycle action was taken.

## Verification

- `python scripts/validate-governance-contract.py`: PASS
- `python -m unittest discover -s tests -v`: PASS — 23 tests
- `bash -n scripts/*.sh`: PASS
- `git diff --check`: PASS
- `scripts/workspace-inventory.sh`: PASS
- `scripts/github-governance-audit.sh`: PASS; audit output kept outside the
  repository under `/tmp`.

## Remaining external decisions

- Apply `governance/github-enforcement-policy.yaml` to GitHub rulesets after
  Founder review.
- Decide how to resolve the eight unreadable/prunable worktree references.
- Copy or link the component contract into each product repository through
  separate reviewed PRs; dirty canonical product checkouts were intentionally
  not modified in this pass.
- Push and rerun the remote CI checks for the draft governance PR.
