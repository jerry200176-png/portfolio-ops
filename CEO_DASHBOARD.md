# CEO Dashboard

Last updated: 2026-07-25 14:30 +08:00 (by `/portfolio-maintain triage`, full
pass — both AllTrue and Sunrise refreshed via GitHub triage and Gmail
signal analysis this run).

## Executive Summary

- Active projects: 2 (AllTrue System, Sunrise Cafe), both Tier 0, both live
  in production.
- **Portfolio-level highest risk (revised this pass): AllTrue issue #1401**
  — a parent-portal cross-student PII exposure affecting minors' data. The
  code fix (PR #1400) is merged, but the production deploy is
  self-reported/unverified and the incident's own containment checklist
  (parent notification, evidence retention, exposure-log review) is
  entirely unexecuted. This outranks the prior top item (AllTrue repo
  visibility) because it is an *active* authorization-boundary bug, not
  historical exposure.
- **AllTrue repo visibility remains unresolved** — the "restored to
  private" claim from the prior pass is still unverifiable/contradicted;
  no tool in this pass's scope could independently confirm current
  visibility. Carried forward, not resolved.
- **New candidate P0**: a GitGuardian 3-secret cluster (Telegram Bot Token,
  Laravel APP_KEY, Bearer Token) flagged 2026-07-17. Not yet confirmed
  whether this duplicates the already-rotated SEC-ALLTRUE-001 set or is a
  new exposure — pending direct secret-scanning confirmation.
- **Sunrise is no longer stale** — fresh triage completed this pass. Two
  findings escalate Sunrise's risk: (1) the Vercel deployment-capacity cap
  now confirmed hitting **production** deploys directly, not just preview;
  (2) issue #211's Founder decisions (FD-1…FD-6: RLS, rate limiting, backup
  posture) were made 2026-07-19 but **zero execution PRs exist since** —
  fail-open rate limiting is confirmed live in production right now.
- Also new: Sunrise's "Agent Session Provenance" CI check is failing
  repeatedly (8x/30 days per Gmail, confirmed as a real failing required
  check on PR #253 via GitHub) — needs log-level triage to classify as a
  CI bug or a genuine policy violation.
- This pass made no code changes, no merges, no deploys, and no visibility
  changes. It is diagnostic only, per `CLAUDE.md`'s Founder decision
  boundary — everything below is queued for Founder decision or a future
  `execute`-mode pass.

## Tier 0 priority ordering (this pass)

1. **AllTrue #1401** — active cross-student PII exposure, containment
   unexecuted. Stop-the-line.
2. **AllTrue repo visibility (SEC-ALLTRUE-003)** — unresolved, historical
   exposure while public.
3. **Sunrise OPS-SUNRISE-001** — Vercel cap now hitting production.
4. **Sunrise SEC-SUNRISE-002** — decided-but-unexecuted RLS/rate-limit/
   backup work; fail-open rate limiting live now.
5. **AllTrue GitGuardian cluster** — candidate P0, pending dedup
   confirmation against SEC-ALLTRUE-001.
6. **Sunrise Agent Session Provenance CI failures** — governance gate,
   needs log triage to determine severity.

## Portfolio Table

| Tier | Product | Production | Git status | CI | Critical work | UX risk | Current action | Next action | Data freshness |
|---|---|---|---|---|---|---|---|---|---|
| 0 | AllTrue System | live, health OK, version `8b4a30f1` (2 commits behind main, normal deploy lag) | main clean, 101 commits behind origin/main locally (not touched) | PR #1400, #1395 merged; PR #1333 confirmed merged (was misreported as "validating_ci") | #1401 containment unexecuted (P0); repo visibility unresolved (P0); GitGuardian cluster pending confirmation (P0); #1096 billing bug, #1100 package-overlap decision (P1) | not assessed this pass | Founder decision on #1401 containment + repo visibility | see Decisions Required | **Fresh — 2026-07-25 14:30, this triage** |
| 0 | Sunrise Cafe | live, health OK; deployed commit confirmed current `origin/main` HEAD (not behind despite stale local checkout) | `chore/dependabot-major-policy` branch, dirty (uncommitted wildcard change, not touched), 7 commits behind origin/main | main CI green; PR #253 failing Agent Session Provenance check | Vercel cap hitting production (P0, escalated); #211 decided-not-executed (P0); provenance CI failures (P1) | medium | none taken this pass | see Decisions Required | **Fresh — 2026-07-25 14:30, this triage** |

## Work Completed (this session)

- AllTrue: GitHub triage and Gmail signal analysis re-run and consolidated.
  Corrected `PROD-ALLTRUE-003` from stale "validating_ci" to confirmed
  merged. Surfaced #1401 (new top P0) and the GitGuardian cluster
  (candidate P0, pending confirmation). Added #1096 and #1100 as tracked
  P1 items. No code changes, no visibility changes, no issue closures.
- Sunrise: full fresh triage completed (previously 6 days stale). Escalated
  the Vercel capacity issue from "preview-only" to "confirmed hitting
  production." Reclassified #211/SEC-SUNRISE-002 from "queued" to
  "decided_not_executed" to reflect that Founder decisions exist but
  nothing has shipped. Added the Agent Session Provenance CI failure
  pattern as a new tracked item. Local uncommitted `dependabot.yml` change
  on `chore/dependabot-major-policy` confirmed structurally identical to
  what's already live on `origin/main` (merged PR #249) — left untouched
  pending Founder/orchestrator confirmation of branch intent.
- `state/work-queue.yaml` and `portfolio.yaml` updated with all findings
  above; see `reports/2026-07-25/github-triage.md` and
  `reports/2026-07-25/gmail-signals.md` for full evidence and score
  rationale.

## Decisions Required

1. **AllTrue #1401 containment** (new, most urgent) — confirm production
   deploy of PR #1400 and execute the incident's containment checklist
   (parent notification, evidence retention, exposure-log review). PII of
   minors, legal-adjacent — this session does not act unilaterally.
2. **AllTrue repository visibility** (carried forward, unresolved) —
   confirm whether it should be private and restore it, or explicitly
   accept public visibility as an intentional tradeoff, given git history
   contains a superseded-but-real database credential.
3. **AllTrue GitGuardian 3-secret cluster** (new candidate P0) — confirm
   whether the 2026-07-17 alerts (Telegram, APP_KEY, Bearer) duplicate the
   already-rotated SEC-ALLTRUE-001 set or represent a new exposure.
4. **Sunrise Vercel production-deployment cap** (escalated) — confirm
   current capacity status directly via Vercel dashboard/API (not yet done
   this pass); decide whether to open a dedicated GitHub issue since #211
   does not cover this.
5. **Sunrise #211 execution** — decide whether to greenlight execution of
   the already-made FD-1…FD-6 decisions (RLS, rate limiting, backup
   posture) as the next `execute`-mode work, given fail-open rate limiting
   is confirmed live in production now.
6. **Sunrise `chore/dependabot-major-policy` branch** — confirm whether
   this branch (uncommitted wildcard dependabot change, content already
   matches merged PR #249) is stale/redundant or represents in-progress
   intent that should continue.
7. **AllTrue DB-password reuse verification** (carried forward) — confirm
   the pre-fix value was never used as a real credential outside ephemeral
   CI; rotate anywhere it was.
8. **portfolio-ops remote** (carried forward) — no GitHub remote is
   configured for this control-plane repo; decide whether to add one
   before a Draft PR can be opened for the restructuring branch.

## Next Highest-ROI Actions (max 5, portfolio-wide)

1. Founder confirms AllTrue #1401 production deploy and executes the
   containment checklist — highest-stakes, PII-of-minors, currently
   entirely unactioned.
2. Founder resolves AllTrue repo visibility (Decision 2) and the
   GitGuardian dedup question (Decision 3) together, since both touch the
   same secret-rotation evidence trail.
3. Direct Vercel dashboard/API check for Sunrise capacity status, followed
   by a Founder go-ahead to execute Sunrise #211's already-decided items
   (RLS, rate limiting, backup posture) via `execute` mode.
4. Log-level triage of Sunrise's Agent Session Provenance CI failures on
   PR #253 to classify as CI bug vs. real policy violation.
5. Founder decision on the `chore/dependabot-major-policy` branch and the
   `portfolio-ops` GitHub remote — both low-effort administrative
   decisions currently blocking cleanup.
