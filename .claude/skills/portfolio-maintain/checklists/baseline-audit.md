# Baseline audit checklist

One repository at a time. Delegate to `portfolio-auditor` for the read-only
survey, and to `ux-reviewer` / `security-reviewer` for their lenses;
`repo-maintainer` only enters after the audit identifies concrete work.

## Before entering the repo

1. Read README, CLAUDE.md/AGENTS.md, CONTRIBUTING, architecture docs,
   runbooks, deployment workflows.
2. Confirm Git state (see `../../../../CLAUDE.md` Git rules).
3. Confirm package manager and lockfile.
4. Confirm test/build/security-scan commands.
5. Confirm no secret or production data will land in output
   (`../../../../docs/security-boundaries.md`).

## Five lenses

**Product** — primary users and core flow; is product value clear;
unfinished/contradictory/duplicate features; do real user reports have an
owner and evidence.

**UX** (`ux-reviewer`) — dead ends in key flows; error messages; loading/
empty/error/success states; permission/state inconsistency; mobile
responsiveness; accessibility; form error-prevention; does the user always
know the next step.

**Engineering** — architecture boundaries; duplicated logic; tests; type/
lint/static analysis; dependency health; migrations; idempotency;
concurrency; error handling; feature flags; rollback readiness.

**Operations** — CI; deploy; health checks; observability; alerts; backups;
runbooks; production version tracking; owner and escalation path.

**Business** — revenue/retention/activation/support-cost/operational-cost
relevance; which technical work actually moves these; what should be
deferred as merely local cleanup.

## Output

Write/refresh a Project Status Card
(`../../../../docs/templates/project-status-card.md`) at
`reports/YYYY-MM-DD/status-cards/<id>.md`, and update the project's row in
`portfolio.yaml`.
