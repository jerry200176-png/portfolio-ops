# CEO Dashboard

Last updated: 2026-07-25 (by `/portfolio-maintain` bootstrap — restructuring
from `company-os`, evidence carried forward from 2026-07-24 state, not a
fresh triage pass). Regenerate via `/portfolio-maintain status` or
`/portfolio-maintain triage` for current facts before trusting stale rows.

## Executive Summary

- Active projects: 2 (AllTrue System, Sunrise Cafe), both Tier 0, both live
  in production.
- Portfolio-level highest risk: **SEC-ALLTRUE-003** — AllTrue was publicly
  visible while a CI credential was exposed in a public Actions log.
  Visibility restored to private and verified; exposed credential treated as
  compromised; containment PR #1395 open with required checks failing as of
  last check (2026-07-24T11:06Z).
- This session's value so far: rebuilt the portfolio control plane
  (`company-os` → `portfolio-ops`) onto a conservative autonomy policy — no
  further product changes made yet in this pass.

## Portfolio Table

| Tier | Product | Production | Git status | CI | Critical work | Gmail signals | UX risk | Current action | Next action |
|---|---|---|---|---|---|---|---|---|---|
| 0 | AllTrue System | live, health OK, version drift vs. last successful deploy (2e715dd1 vs 5911a90) as of 2026-07-24 | canonical clean at last check | PR #1395 required checks failing (Agent Session Provenance, Presubmit Checks) | SEC-ALLTRUE-003 credential containment | GitGuardian-class alerts historically high-signal here | medium | repair PR #1395 gates | Founder merge decision once green |
| 0 | Sunrise Cafe | live, health OK, version matched `origin/main` at last check | canonical clean at last check | main CI green at last check | SEC-SUNRISE-002 RLS/rate-limit/backup decision queue | Vercel capacity-limit mail | medium | confirm current Vercel preview capacity | resume SEC-SUNRISE-002 with fresh evidence |

Facts above are inherited from `state/work-queue.yaml` as of 2026-07-24 and
have **not** been re-verified in this session. Run `/portfolio-maintain
triage` before acting on them.

## Work Completed (this session)

- Repository: `portfolio-ops` (control plane, not a product)
  - Restructured `company-os` → `portfolio-ops`, git history preserved.
  - Rewrote `governance/AUTONOMY_POLICY.md` and the Authority section of
    `governance/COMPANY_CONSTITUTION.md`: revoked autonomous merge/deploy/
    production-data-mutation/Gmail-mutation/history-rewrite authority.
  - Added `CLAUDE.md`, `portfolio.yaml` + schema, `PORTFOLIO.md`,
    `docs/*`, `.claude/skills/portfolio-maintain/`, `.claude/agents/*`,
    `.claude/settings.json` + hooks.
  - No product repository (AllTrue, Sunrise) was touched.
  - Unverified: hooks have been tested against a dummy repo and a read-only
    command sample, not against a live product repo.

## Decisions Required

1. **AllTrue PR #1395** (SEC-ALLTRUE-003 containment) — once required checks
   pass, this needs a Founder merge decision; it removes a hard-coded CI
   credential path. Do not merge without re-verifying checks are green.
2. **Sunrise Vercel capacity** — if preview-deployment capacity is still
   limited, decide whether to wait, escalate the plan/billing limit, or
   route around it for the next release.
3. **portfolio-ops autonomy rewrite** — confirm the new conservative
   `AUTONOMY_POLICY.md` (this session's change) matches intent going
   forward; it replaces a broader autonomous-merge/deploy grant that was
   live until today.

## Next Highest-ROI Actions (max 5, portfolio-wide)

1. Run `/portfolio-maintain triage` on AllTrue to re-verify PR #1395 gate
   status with fresh evidence before any merge decision.
2. Re-check Sunrise Vercel/Actions capacity; unblock SEC-SUNRISE-002 if
   capacity has recovered.
3. Run a baseline audit (`/portfolio-maintain execute`, product/UX/
   engineering/operations/business lenses) on whichever of the two Tier 0
   products has gone longer without one.
4. Read 90 days of Gmail signals for both products via `gmail-signal-analyst`
   to refresh the triage report — last full pass was 2026-07-19.
5. Validate the new hooks in `.claude/settings.json` against each product
   repo's actual workflow (not just the dummy repo) before relying on them.
