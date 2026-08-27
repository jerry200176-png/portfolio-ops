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
| Release evidence automation | `scripts/release-evidence.py` + `tests/test_release_evidence.py` | Read-only, machine-readable proof that health is good and the serving SHA matches the intended release |
| Recovery | rollback-readiness checks and guarded operation workflows | Keep data repairs and production mutations explicit, reversible, and audited |

## Tool selection decisions

The following choices are based on the current AllTrue stack and the tools
already wired into its repositories. They are the default path for future
tasks:

| Decision | Tool | Why it fits AllTrue | Evidence / entry point |
|---|---|---|---|
| Adopt now | GitHub Actions + `gh` | PR checks, review state, release workflows, and read-back are already the system's authoritative collaboration boundary | `.github/workflows/`, PR #2086, Portfolio `state/work-queue.yaml` |
| Adopt now | Playwright | Tests the director's real page and interaction sequence, including asynchronous races that unit tests cannot see | `frontend/e2e/`, PR #2086 delayed-422 scenario |
| Adopt now | ExoProtocol + agent-control | Isolates worktrees, records provenance, and blocks unsafe workspace operations before product edits | `agent-control/`, `exo check`, `workspace.manifest.yaml` |
| Adopt now | CodeQL, gitleaks, OpenSSF Scorecard, Dependabot | Existing layered security and dependency controls cover source, secrets, supply chain, and update drift without adding a duplicate scanner | AllTrue and Portfolio required checks |
| Adopt now | Portfolio release evidence | Makes health and serving-commit identity a machine-checkable release gate | `scripts/release-evidence.py` |
| Defer | Sentry / hosted error tracking | Useful only after an explicit PII/minor-data retention policy, account ownership, and production integration plan exist | No approved integration or retention decision in the current portfolio |
| Defer | OpenTelemetry collector | Valuable for distributed traces, but the current self-hosted deployment needs a storage, sampling, and retention design before emitting operational data | No approved trace schema or retention budget |
| Do not add yet | Renovate or Semgrep as parallel defaults | Dependabot and CodeQL already cover the corresponding baseline classes; a second always-on tool would add noise unless a measured gap is documented | Existing workflow inventory and quality gates |
| Defer | Backstage portal | The catalog is already Backstage-compatible; a portal is unnecessary overhead until the portfolio grows beyond the current operating scale | `catalog/*.yaml`, `docs/workspace-operating-model.md` |

### Import rule

An additional tool may enter the default toolchain only when a concrete
incident or measured coverage gap names the missing control, the repository
owner and data-retention impact are known, and the tool can emit evidence into
the Portfolio work queue. This keeps the loop self-improving without turning
tool installation into an unreviewed production change.

## Current gap to close

AllTrue has many task worktrees and useful tests, but the user-facing incident
loop was previously missing the last mile: capture the director’s failed
workflow, identify the exact response race, fix the interaction, run the
regression suite, deploy, and re-check the production identity. PR #2086 now
contains that path up to the review gate. Its head `4af00816` also includes a
real Vue page-level Playwright scenario that deliberately delays an old 422 and
proves the director's newer successful date remains actionable.

## Next system-level improvements

1. Add an authenticated, post-deploy Playwright acceptance scenario for the
   manual-session modal; the deterministic mocked scenario is now covered in
   PR #2086, but production credentials and a live verification trace remain
   intentionally separate.
2. Standardize a small frontend API/request-state helper so every async
   decision modal gets request ordering, cancellation, retry, and structured
   error display by default.
3. Use Portfolio freshness as a required release input: stale evidence blocks
   closure claims and deployment authorization. Run `scripts/release-evidence.py`
   after deployment so a fresh report links the exact PR, CI run, production
   identity, and post-deploy smoke.
4. Keep folder cleanup proposal-only until each legacy or dirty worktree has an
   owner, recoverability evidence, and explicit archive/remove approval.
