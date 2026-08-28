# Platform Optimization Baseline — 2026-08-01

## Scope

- Products: `jerry200176-png/AllTrue_System`, `jerry200176-png/sunrise-cafe`
- Control plane: `portfolio-ops`
- Mode: baseline, isolated implementation, required-CI verification, controlled merge/deploy, and read-only production evidence. Founder-only privacy and credential decisions remain untouched.

## Live execution evidence (2026-08-01)

| Product | Merged change | Production evidence | Rollback evidence |
|---|---|---|---|
| AllTrue | #1579 (`0fef175a…`) then #1580 (`510f6b2e…`) | Deploy run [30685651049](https://github.com/jerry200176-png/AllTrue_System/actions/runs/30685651049) passed; backup completed; `security_audit_events` migration passed; read-only smoke passed; `deployment.json` backend SHA and `/api/v1/health` matched. | Workflow rollback path was validated by CI readiness checks; no rollback was needed. |
| Sunrise | #267 (`6605204e…`) | Deploy run [30685328910](https://github.com/jerry200176-png/sunrise-cafe/actions/runs/30685328910) and read-only verify run [30685328925](https://github.com/jerry200176-png/sunrise-cafe/actions/runs/30685328925) passed; `/api/version` matched and `/api/booking-health` returned `ok`. | No rollback was needed; production deploy completed successfully. |
| Portfolio | #27 (`4e3968b3…`) | Control-plane checks (validate, CodeQL, Secret scan, OpenSSF Scorecard) passed before merge. | Documentation/YAML-only change; revert is sufficient. |

The live Sunrise health response still reports `rate_limit_mode=memory`, `rate_limit_grade=degraded_per_isolate`, and `stripe_enabled=false`; these remain explicit follow-up evidence for #211.

## Evidence

| Area | Observation | Source |
|---|---|---|
| AllTrue checkout | Canonical checkout was clean on `main` but 134 commits behind `origin/main`; an isolated worktree was created from `origin/main` at `01a34ae2`. | local `git status`, `git fetch`, `git worktree add` |
| Sunrise checkout | Existing `chore/dependabot-major-policy` branch contains an uncommitted `.github/dependabot.yml`; it was preserved untouched. | local `git status` |
| Portfolio checkout | Existing untracked `reports/codex/` was preserved untouched; isolated worktree created from `origin/main` at `ded893b`. | local `git status`, `git worktree add` |
| AllTrue board | #1408 still listed #1402, #1409, and #1410 as open even though the PRs are merged. | GitHub issue #1408 |
| AllTrue reliability | #1420 identifies missing audit history for parent auth, sibling switching, and notification binding; #1428 identifies stale frontend-only deployment identity. | GitHub issues #1420, #1428 |
| Sunrise reliability | #211 remains decided-but-unexecuted; #257 requires a single deploy owner; #261 requires a reproducible typecheck gate. | GitHub issues #211, #257, #261 |
| Reference research | Existing RFC already maps starred repositories to bounded adoption hypotheses and explicitly rejects framework rewrites. | `docs/architecture/RFC_PLATFORM_OPTIMIZATION_FROM_STARS_2026.md` |

## Priority decision

Founder-only incident actions remain visible but are not disguised as agent work:

1. AllTrue #1401 manual privacy review and #1387 live credential rotation.
2. AllTrue #1420 auditability and #1428 release identity as bounded Draft PRs.
3. Sunrise #211 code-side hardening, #257 deploy ownership, and #261 typecheck baseline.
4. Architecture and UX epics only after the reliability gates have evidence.

## Draft PR execution evidence

| Slice | Draft PR | Local verification | Live verification |
|---|---|---|---|
| AllTrue #1428 runtime deployment identity | [#1579](https://github.com/jerry200176-png/AllTrue_System/pull/1579) | Required checks passed; production deploy and SHA/health/smoke evidence recorded above. | Workflow rollback path remained available and was not invoked. |
| Sunrise #261 TypeScript baseline | [#267](https://github.com/jerry200176-png/sunrise-cafe/pull/267) | Baseline gate passed; Vitest 344 passed/1 skipped; production deploy and read-only verify passed. | Production deploy completed successfully; no rollback was needed. |
| Sunrise #257 deploy ownership | [#258](https://github.com/jerry200176-png/sunrise-cafe/pull/258) | `npm run verify:production-workflow` passed; current main has read-only verification and one serialized deploy owner. | Vercel project ownership and live behavior require read-only Founder/dashboard verification. |
| AllTrue #1420 security audit trail | [#1580](https://github.com/jerry200176-png/AllTrue_System/pull/1580) | Required checks passed, including PHPStan and full PHPUnit; production backup, migration, deployment identity, and read-only smoke passed. | Normal code revert plus migration rollback procedure remains documented; no rollback was needed. |

The portfolio control-plane update is merged in [PR #27](https://github.com/jerry200176-png/portfolio-ops/pull/27). The next implementer must append new live evidence after each production release; do not mark #1401, #1387, or #211 complete from deployment health alone.

## Handoff

The next implementer should preserve the original dirty checkouts, work on one repository at a time, and follow `triage → baseline audit → single-repo execute → Draft PR → independent evidence verification → merge/deploy → live manifest/health/smoke → dashboard update`. Production migrations, paid-plan changes, issue closure, and legal/privacy decisions remain Founder-gated.
