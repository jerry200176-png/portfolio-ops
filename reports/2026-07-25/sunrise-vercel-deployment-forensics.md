# Sunrise Cafe — Vercel Deployment Forensics

Read-only investigation. No Vercel billing change, no deploy, no merge in
`sunrise-cafe`. Source: GitHub's Deployments API (cross-referencing
Vercel's own GitHub App integration reporting), since this session has no
Vercel dashboard/API credentials — several answers below are therefore
scoped to "what GitHub's record of Vercel's activity shows," not Vercel's
own account/billing data, which the Founder would need to confirm directly.

## Findings

1. **Plan/team/project IDs**: not directly queryable (no Vercel
   credentials). The account/team slug visible via deployment URLs is
   `jerry200176-6960s-projects`. **At least 4 distinct Vercel project
   names** have deployed from this repo historically: `sunrise-cafe`,
   `sunrise-cafe-pklg`, an unlabeled legacy `Production`/`Preview` project,
   and a short-lived `workspace` / `workspace-1783862318827-c3Jm` pair.
2. **Deployments/day, last 30 days** (351 total across 9 active days):
   07-09: 16, 07-10: 54, 07-11: 116, 07-12: 103, 07-13: 12, 07-14: 11,
   07-18: 23, 07-19: 8, 07-24: 8.
3. **Production vs. preview**: roughly even over the full lifetime —
   production 353 (`sunrise-cafe` 146 + `sunrise-cafe-pklg` 152 + legacy
   55), preview 288 (143 + 137 + 8).
4. **Trigger source**: 647/653 (99%) created by `vercel[bot]` — Vercel's
   native GitHub App integration reacting directly to push/PR events, not
   GitHub Actions. Only 6 came from the CLI fallback in
   `scripts/orchestrator/deploy.sh` (`npx vercel deploy --prod --token`),
   triggered by `verify-production.yml` when production doesn't match
   `main`'s SHA within 90 seconds of a push.
5. **Biggest contributor**: structural duplication, not a branch/bot/commit
   type. `sunrise-cafe` and `sunrise-cafe-pklg` both started deploying the
   same day (2026-02-24 production, 2026-04-24 preview) and have run in
   lockstep since — every push has gone to both. A third, legacy unlabeled
   project ran alongside them until 2026-07-18. A fourth (`workspace`/
   `workspace-<id>`) appeared for exactly one day (07-12), matching that
   day's spike to 103 deployments.
6. **Same commit deployed repeatedly**: confirmed. Commit `9ac7da6` has
   separate deployment records for `Production – sunrise-cafe` (id
   `5588094008`) and `Production – sunrise-cafe-pklg` (id `5588058176`),
   3 minutes apart.
7. **Multiple Vercel projects on one repo**: **yes, confirmed** — the core
   finding. `sunrise-cafe` → `sunrise-cafe-*.vercel.app`,
   `sunrise-cafe-pklg` → `sunrise-cafe-pklg-*.vercel.app`, same team, both
   auto-deploying via GitHub integration on every push.
8. **Does `ignoreCommand` skip no-impact commits?** Partially.
   `scripts/vercel-ignored-build.sh` correctly skips the *build* for any
   non-production `VERCEL_ENV` (saves build minutes), but does not reduce
   the *deployment record count* — a deployment is created and quota-
   counted the moment Vercel receives the push event, before
   `ignoreCommand` is evaluated. It mitigates build-minute waste, not the
   "Resource is limited" deployment-count cap.
9. **PR #203/#206 mitigation status**: effective at what they targeted
   (cron frequency, hourly → 6h) but never addressed the duplicate-project
   linkage or the auto-redeploy-on-drift logic — they solved an adjacent
   problem, not this one.
10. **Actual production/user impact**: production has stayed current
    (confirmed earlier this session — deployed commit matches
    `origin/main` HEAD). Impact so far is latent risk + wasted signal, not
    confirmed downtime: `verify-production.yml` going red under quota
    pressure, and a self-reinforcing loop where quota exhaustion slows
    native deploys, which makes the 90-second drift check fire more often,
    consuming more quota. Real risk materializes the day an urgent fix
    needs to ship during a quota-exhausted window.

## Classification

**Mixed cause**, two confirmed, independent, compounding mechanisms:

1. **Vercel configuration problem (primary, quantifiable)** — 2-4 Vercel
   projects linked via GitHub App integration to one repo, under one
   shared-quota team account, multiplying every push's deployment count.
2. **GitHub automation problem (secondary, self-reinforcing)** —
   `verify-production.yml`'s auto-redeploy-on-drift can't distinguish
   "quota-throttled" from "genuinely stuck," so it's more likely to fire
   (adding more load) exactly when the system is already strained.

Not "legitimate volume exceeding Hobby" — volume is inflated by
duplication, not organically over the limit.

## Durable remediation plan

1. **Eliminate unnecessary deployments**: Founder identifies which project
   serves `sunrise-cafe-six.vercel.app` in the Vercel dashboard and
   disconnects GitHub auto-deploy from the others (`sunrise-cafe-pklg` at
   minimum; the legacy/`workspace` ones look already-abandoned — confirm
   and delete). Likely cuts deployment count by 50%+ with zero code change.
2. **Avoid recurrence**: document "one repo → one Vercel project"; fix
   `verify-production.yml` to back off (not retrigger) when the CLI
   fallback reports `deploy_rate_limited`, and rate-limit the auto-redeploy
   trigger itself (e.g., max once/hour, not once/push).
3. **Pro upgrade**: not justified yet. Fix duplication first, remeasure
   real single-project volume for 1-2 weeks, then decide — upgrading now
   would let Pro's higher cap mask the duplicate-project bug rather than
   fix it.
4. **Cost/limits before/after**: not answerable from this session (no
   Vercel dashboard access) — confirm current Hobby vs. Pro deployment
   caps and Pro's per-seat cost directly on vercel.com/pricing.
5. **Verification plan**: after disconnecting duplicate projects and
   fixing the retry logic, monitor the GitHub Deployments API daily count
   for 1-2 weeks; confirm it drops roughly proportional to projects
   removed and zero `Resource is limited` errors recur.
