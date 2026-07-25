# CEO Dashboard

Last updated: 2026-07-25 13:07 +08:00 (by `/portfolio-maintain triage`,
scoped to AllTrue SEC-ALLTRUE-003 only, per Founder instruction — Sunrise
row below is a staleness flag only, not a fresh triage).

## Executive Summary

- Active projects: 2 (AllTrue System, Sunrise Cafe), both Tier 0, both live
  in production.
- Portfolio-level highest risk: **AllTrue repository is currently PUBLIC**
  (confirmed via live GitHub API check), contradicting the prior claim that
  visibility had been restored to private. Git history contains a pre-fix
  plaintext database password (now superseded in code, rotation status at
  any real point of use unconfirmed). See
  `reports/2026-07-25/alltrue-sec-1387-incident-status-card.md`. This is
  more urgent than the original SEC-ALLTRUE-003 code-fix question, which is
  already resolved (PR #1395 merged, CI green).
- This session's value so far: rebuilt the portfolio control plane
  (`company-os` → `portfolio-ops`), persisted it to a branch with a secret
  scan, adversarially hardened the PreToolUse hooks (found and fixed real
  bypasses), and ran a scoped incident triage that corrected two stale
  facts and surfaced one new live risk. No AllTrue/Sunrise code was
  changed; no merge/deploy/visibility-change was performed.

## Portfolio Table

| Tier | Product | Production | Git status | CI | Critical work | UX risk | Current action | Next action | Data freshness |
|---|---|---|---|---|---|---|---|---|---|
| 0 | AllTrue System | live, health OK, version `8b4a30f1` (2 commits behind main `97f2e611`, normal deploy lag) | not checked this pass (GitHub-only triage) | PR #1395 merged, all 20 checks green | Repo is public (new finding); DB-password rotation/reuse unconfirmed; issue #1387 open | not assessed this pass | Founder decision on repo visibility | see Decisions Required | **Fresh — 2026-07-25 13:07, this triage** |
| 0 | Sunrise Cafe | live, health OK at last check | not checked this pass | main CI green at last check (2026-07-19) | SEC-SUNRISE-002 RLS/rate-limit/backup decision queue; Vercel capacity-limit mail | medium (last assessed 2026-07-19) | none taken this pass — explicitly out of scope | resume `/portfolio-maintain triage` on Sunrise once AllTrue P0 is closed | **STALE — 6 days old (last real check 2026-07-19), do not act on this row without re-triaging** |

Per instruction, this pass did not touch Sunrise beyond flagging staleness.
AllTrue containment took priority; no Sunrise code work should start before
the AllTrue P0 above reaches Founder closure.

## Work Completed (this session)

- Repository: `portfolio-ops` (control plane, not a product)
  - Restructured `company-os` → `portfolio-ops`, git history preserved.
  - Branch `chore/portfolio-maintenance-os`: secret-scanned, committed the
    full restructuring (architecture, skill, agents, hooks, governance,
    schemas, dashboard, carried-forward evidence). No `origin` remote
    configured, so not pushed and no Draft PR opened yet — Founder decision
    needed on whether/where to add a remote.
  - Adversarially tested `.claude/hooks/guard_bash.py` and `deny_tool.py`:
    found and fixed real bypasses (`git -C` flag insertion, Python-list-
    literal token separation, generic deploy scripts, symlink-indirected
    credential reads, a missing Gmail `update_label` mutation tool) and one
    false positive (a commit message mentioning "deploy"). Full results:
    `docs/hook-threat-model.md`. **Caveat**: live end-to-end hook firing in
    this session was not confirmed — likely needs `/hooks` reload or a
    fresh session (see threat model doc).
  - No product repository (AllTrue, Sunrise) was touched.
- AllTrue System: read-only triage only, no code changes. See Incident
  Status Card: `reports/2026-07-25/alltrue-sec-1387-incident-status-card.md`.
  Corrected `state/work-queue.yaml` and `portfolio.yaml` to reflect that
  PR #1395 is merged (not open/failing as previously recorded) and added
  the new repo-visibility finding.

## Decisions Required

1. **AllTrue repository visibility** (new, most urgent) — confirm whether
   it should be private and restore it, or explicitly accept public
   visibility as an intentional tradeoff (e.g., for GitHub Actions minutes)
   given git history contains a superseded-but-real database credential.
2. **AllTrue DB-password reuse verification** — confirm the pre-fix value
   was never used as a real credential outside ephemeral CI; rotate
   anywhere it was. Not yet confirmed either way.
3. **AllTrue Actions-log residual exposure** — decide whether to accept run
   `30086225720`'s log as residual risk or take GitHub action on it.
4. **Issue #1387 closure** — close only once 1–3 are addressed; this
   session does not close issues.
5. **portfolio-ops remote** — no GitHub remote is configured for this
   control-plane repo; decide whether to add one (and its visibility)
   before a Draft PR can be opened for the restructuring branch.
6. **Sunrise Vercel capacity / SEC-SUNRISE-002** — carried forward, still
   unresolved, intentionally not touched this pass (6 days stale — needs a
   fresh triage before any action).

## Next Highest-ROI Actions (max 5, portfolio-wide)

1. Founder resolves AllTrue repo visibility (Decision 1) — highest-leverage
   single action available right now.
2. Founder or a follow-up session confirms DB-password non-reuse (Decision
   2) and closes issue #1387 with evidence.
3. Re-run `/portfolio-maintain triage` on Sunrise (currently 6 days stale)
   before any Sunrise work begins.
4. Confirm the portfolio-ops hooks actually fire live (open `/hooks` or
   start a fresh session, then re-run the throwaway-repo proof in
   `docs/hook-threat-model.md`).
5. Decide on a `portfolio-ops` GitHub remote so the restructuring branch
   can get a real Draft PR instead of sitting local-only.
