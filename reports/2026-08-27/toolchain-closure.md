# Toolchain and closed-loop operating model — 2026-08-27

Cloudflare is useful for edge/network/browser capabilities, but it is not the
only control needed to improve AllTrue. The workspace already contains a
stronger multi-layer loop:

| Layer | Existing tool / source | Role in the loop |
|---|---|---|
| Task isolation | `agent-control/bin/agent-start`, ExoProtocol | One repository, branch, worktree, ticket, and manifest per change |
| Portfolio control | `portfolio.yaml`, `state/work-queue.yaml`, `portfolio-freshness.py` | Current priority, evidence TTL, owner, rollback, and next action |
| Workspace hygiene | `workspace-inventory.sh` | Detect dirty, stale, legacy, and unresolved checkouts without destructive cleanup |
| Backend correctness | PHPUnit, PHPStan, Laravel feature tests | Capacity, authorization, domain invariants, and regression coverage |
| Frontend correctness | Vitest, Vite build, Playwright UI smoke | Component behavior, build integrity, and real-page interaction coverage |
| Supply-chain/security | gitleaks, Composer/npm audit, governance and security workflows | Prevent secret and dependency regressions from entering release paths |
| Release identity | `version.json`, `deployment.json`, health/smoke workflows | Prove what is serving after merge, rather than trusting a green PR |
| Recovery | rollback-readiness checks and guarded operation workflows | Keep data repairs and production mutations explicit, reversible, and audited |

## Current gap to close

AllTrue has many task worktrees and useful tests, but the user-facing incident
loop was previously missing the last mile: capture the director’s failed
workflow, identify the exact response race, fix the interaction, run the
regression suite, deploy, and re-check the production identity. PR #2086 now
contains that path up to the review gate.

## Next system-level improvements

1. Add an authenticated Playwright scenario for the manual-session modal that
   proves an older failed check cannot replace a newer successful check.
2. Standardize a small frontend API/request-state helper so every async
   decision modal gets request ordering, cancellation, retry, and structured
   error display by default.
3. Use Portfolio freshness as a required release input: stale evidence blocks
   closure claims and deployment authorization, while a fresh report links the
   exact PR, CI run, production identity, and post-deploy smoke.
4. Keep folder cleanup proposal-only until each legacy or dirty worktree has an
   owner, recoverability evidence, and explicit archive/remove approval.
