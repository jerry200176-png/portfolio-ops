# Platform Optimization Baseline — 2026-08-01

## Scope

- Products: `jerry200176-png/AllTrue_System`, `jerry200176-png/sunrise-cafe`
- Control plane: `portfolio-ops`
- Mode: read-only triage plus Draft-PR preparation; no merge, deploy, production data mutation, credential rotation, or issue closure.

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

## Handoff

The next implementer should use the isolated worktrees, preserve the original dirty checkouts, work on one repository at a time, and stop each change at Draft PR plus independent evidence verification. Production migrations, paid-plan changes, merge, deploy, issue closure, and legal/privacy decisions require Founder action.
