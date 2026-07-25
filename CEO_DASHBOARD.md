# CEO Dashboard

Last updated: 2026-07-25 ~22:00 +08:00 (Claude Code instructions-
architecture audit merged; Portfolio OS optimization work now stopped —
next session moves to AllTrue #1401 containment. See the new section
immediately below, then "2026-07-25 round 2" for prior same-day work).

## 2026-07-25 — Claude Code instructions-architecture audit (portfolio-ops itself)

Three-phase audit of this repo's own instruction architecture (CLAUDE.md,
`.claude/rules/`, Skills, Subagents, Hooks/Permissions, auto memory),
grounded in current official Claude Code docs fetched live this session —
merged as [PR #6](https://github.com/jerry200176-png/portfolio-ops/pull/6)
(commit `2492bed`, merge commit `d4ebc66`). Founder-approved after
re-verifying head commit, file scope, secret scan, and regression tests
immediately before merge.

- CLAUDE.md was already under the official 200-line guidance and correctly
  scoped — not blindly shortened; grew +4 lines to close a real gap (no
  rule previously existed stating safety policy/production boundaries/Git
  destructive-operation controls must never move to auto memory).
- Added `.claude/rules/` (didn't exist before): path-scoped conventions for
  agent definitions and portfolio-state YAML schema — zero fixed context
  cost, load only on matching files.
- Added `permissions.deny` to `.claude/settings.json` (6 literal
  destructive-command patterns) as a defense-in-depth layer alongside the
  existing `guard_bash.py`/`deny_tool.py` hooks, per official guidance that
  hook-based Bash pattern-matching is best-effort/fail-open — hooks
  unchanged, nothing replaced.
- Collapsed a 3-way redundant restatement of the Never-list (CLAUDE.md,
  `AUTONOMY_POLICY.md`, `COMPANY_CONSTITUTION.md`) to one authoritative
  source + one always-on summary + one pointer; trimmed a duplicated
  procedure block in `docs/operating-model.md`; fixed two dead file
  references.
- Verified before merge: hook regression suite green (18 safe + 38
  dangerous), `settings.json` valid JSON, all 7 read-only agents still
  lack `Write`/only `repo-maintainer` has it, `/portfolio-maintain status`
  resolves end-to-end, full diff secret-scanned clean, no product repo /
  incident evidence / autonomy / merge / deploy / agent-write boundary
  touched.

**Portfolio OS optimization work stops here for this session** — no
further Star-cleanup, reference-schema, or provenance-redesign follow-up
unless a real defect surfaces. Next: AllTrue #1401 containment (single
Tier-0 item), in `AllTrue_System` only.

## 2026-07-25 round 2 — AllTrue #1387 containment, Portfolio OS merge, priority reorder

- **AllTrue #1387: 4 of 5 Founder closure conditions now met.** Repo
  private ✅, replacement verified ✅ (CI-side), Actions-log exposure
  removed ✅ (run `30086225720` logs deleted, verified 404; artifacts
  precisely checked — clean, untouched), evidence documented ✅. The one
  remaining blocker — confirming the leaked DB password was never real/
  reused in production — has its verification tool built and tested
  (AllTrue_System PR [#1414](https://github.com/jerry200176-png/AllTrue_System/pull/1414),
  Draft, not merged) but **cannot run yet**: GitHub requires
  `workflow_dispatch` workflows to exist on the default branch before
  they're triggerable, which requires either merging #1414 (outside this
  session's product-repo merge authority) or a direct push to `main`
  (forbidden). **Recommendation revised to NOT READY TO CLOSE** — Founder
  merging #1414 and running it is the single remaining action.
- **GitHub personal Security log**: no programmatic access exists (3
  endpoint shapes tried, all 404) — this is an Enterprise/org-only API
  surface. Founder must check `github.com/settings/security-log` directly
  if the visibility-change root cause matters.
- **Portfolio OS PR #1**: merged (commit `3f325cbd`) after fixing a second
  hook false-positive (descriptive text in PR bodies/commit messages was
  being denied as if it were a real command — fixed narrowly, regression-
  tested both directions, live-proved in a throwaway repo) and a clean
  full-diff secret scan. Local `main` fast-forwarded, working tree clean.
- **Priority reorder** (AllTrue #1401 vs. Sunrise Vercel cap vs. Sunrise
  Agent Session Provenance CI): #1401 remains the single highest-severity
  item (PII of minors) but its remaining work is Founder-only (legal/
  notification), not something `execute` mode (Draft-PR engineering work)
  can act on. Comparing the other two on actual user/production impact and
  ongoing recurrence: the Vercel deployment cap is recurring across
  multiple dates and hits **production** directly (blocking releases,
  including future fixes), while the Provenance CI failures — though also
  recurring — have no end-user impact, only an internal governance gate.
  **Selected for `execute`: Sunrise Vercel deployment-capacity cap.**
  Caveat found during selection: this project is on Vercel's Hobby (free)
  tier and has already iterated on code-side mitigations (`ignoreCommand`,
  cron-frequency reductions in PRs #203/#206) — the durable fix may turn
  out to be a Founder billing decision (plan upgrade) rather than pure
  code, but a further code-side reduction in build/deploy volume hasn't
  been fully explored yet and is this session's next concrete step if
  continued.

## Executive Summary

- Active projects: 2 (AllTrue System, Sunrise Cafe), both Tier 0, both live
  in production.
- **Portfolio-level highest risk (revised this pass): AllTrue issue #1401**
  — a parent-portal cross-student PII exposure affecting minors' data. The
  code fix (PR #1400) is merged, but the production deploy is
  self-reported/unverified and the incident's own containment checklist
  (parent notification, evidence retention, exposure-log review) is
  entirely unexecuted. This outranks SEC-ALLTRUE-003 (below) because it is
  an *active* authorization-boundary bug, not a now-contained historical
  exposure.
- **AllTrue repo visibility — RESOLVED this pass, with explicit Founder
  approval given live in this session.** `AllTrue_System` is now private
  (changed via `gh api`, independently re-verified with a fresh read: 0
  forks, 0 releases, Pages disabled — no other public surface found). The
  one remaining blocker to closing issue #1387 is credential-reuse
  verification (was the exposed DB password ever real/used outside
  ephemeral CI) — this session has no tool access to DB/provider audit
  logs to confirm that either way. Full exposure inventory, unauthorized-
  use assessment, and history-cleanup impact analysis:
  `reports/2026-07-25/alltrue-sec-1387-incident-status-card.md` §16–19.
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
- **Portfolio OS**: created private repo `jerry200176-png/portfolio-ops`
  (Founder-approved), pushed `main` and `chore/portfolio-maintenance-os`,
  opened Draft PR [#1](https://github.com/jerry200176-png/portfolio-ops/pull/1)
  — not merged. Along the way, a real hook false-positive was found and
  worked around without weakening the hook: `guard_bash.py` blocked a `gh
  pr create` call because the PR body's own *description* of the hook's
  blocking rules contained the literal substring "git reset --hard" —
  fixed by rephrasing the text, not by touching the hook. Hook live-
  blocking was separately proven in a disposable throwaway repo this
  session (created and destroyed within scratchpad only).
- This pass made two irreversible-adjacent changes (repo visibility,
  new-repo creation/push/PR) **only after explicit Founder approval given
  live in this conversation** — an earlier "stop hook feedback" message
  that asserted approval had already been granted was treated as untrusted
  and not acted on until the Founder confirmed directly. No merges, no
  deploys, no production-data changes, no issue closures were performed.

## Tier 0 priority ordering (this pass)

1. **AllTrue #1401** — active cross-student PII exposure, containment
   unexecuted. Stop-the-line.
2. **Sunrise OPS-SUNRISE-001** — Vercel cap now hitting production.
3. **Sunrise SEC-SUNRISE-002** — decided-but-unexecuted RLS/rate-limit/
   backup work; fail-open rate limiting live now.
4. **AllTrue GitGuardian cluster** — candidate P0, pending dedup
   confirmation against SEC-ALLTRUE-001.
5. **AllTrue SEC-ALLTRUE-003** — visibility RESOLVED this pass; only
   credential-reuse verification remains, treated as lower urgency now
   that public exposure is closed.
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
  P1 items.
  **With explicit Founder approval given live in this session**: changed
  `AllTrue_System` from public to private, re-verified, confirmed no other
  public surface (0 forks/releases, Pages disabled). Completed a full
  exposure inventory (branches/tags/code-search/Actions artifacts),
  unauthorized-use assessment (confirmed evidence vs. absence-of-evidence
  vs. unavailable evidence, explicitly), and a history-cleanup impact
  assessment (documented, no rewrite performed). Proposed — but did not
  execute — an Actions-log deletion candidate for run `30086225720`. Full
  detail: `reports/2026-07-25/alltrue-sec-1387-incident-status-card.md`
  §16–19. Recommendation on issue #1387 revised to **READY TO CLOSE WITH
  EXPLICIT RESIDUAL RISK** (credential-reuse verification still open) —
  this session did not close the issue.
- Sunrise: full fresh triage completed (previously 6 days stale). Escalated
  the Vercel capacity issue from "preview-only" to "confirmed hitting
  production." Reclassified #211/SEC-SUNRISE-002 from "queued" to
  "decided_not_executed" to reflect that Founder decisions exist but
  nothing has shipped. Added the Agent Session Provenance CI failure
  pattern as a new tracked item. Local uncommitted `dependabot.yml` change
  on `chore/dependabot-major-policy` confirmed structurally identical to
  what's already live on `origin/main` (merged PR #249) — left untouched
  pending Founder/orchestrator confirmation of branch intent.
- Portfolio OS: **with explicit Founder approval given live in this
  session**, created private repo `jerry200176-png/portfolio-ops`, pushed
  `main` and `chore/portfolio-maintenance-os`, opened Draft PR
  [#1](https://github.com/jerry200176-png/portfolio-ops/pull/1) covering
  architecture, skill/agent/hook design, tests, threat model, rollback,
  and known limitations. Not merged. Diff was reviewed for secret patterns
  before pushing (none found — only type-name references in evidence
  text).
- Hook robustness: found and worked around (without weakening) a
  `guard_bash.py` false positive — a PR-body *description* of the hook's
  own blocking rules literally containing "git reset --hard" was flagged
  as if it were a real command. Confirmed live hook-blocking separately in
  a disposable throwaway repo (created/destroyed in scratchpad only).
- `state/work-queue.yaml` and `portfolio.yaml` updated with all findings
  above; see `reports/2026-07-25/github-triage.md` and
  `reports/2026-07-25/gmail-signals.md` for full evidence and score
  rationale.

## Decisions Required

1. **AllTrue #1401 containment** (most urgent) — confirm production
   deploy of PR #1400 and execute the incident's containment checklist
   (parent notification, evidence retention, exposure-log review). PII of
   minors, legal-adjacent — this session does not act unilaterally.
2. ~~AllTrue repository visibility~~ — **RESOLVED this pass** (private,
   re-verified, no other public surface found).
3. **AllTrue credential-reuse verification** (now the sole blocker on
   SEC-ALLTRUE-003) — confirm the pre-fix DB password was never used as a
   real credential outside ephemeral CI; rotate anywhere it was. No tool
   in this session can check DB/provider audit logs — needs Founder or an
   ops-side check.
4. **AllTrue Actions-log residual exposure** — decide whether to accept
   run `30086225720`'s log as residual risk or delete it (proposed
   deletion list in the incident card §17; nothing deleted).
5. **Issue #1387 closure** — this session's recommendation is READY TO
   CLOSE WITH EXPLICIT RESIDUAL RISK (if Decision 3's risk is accepted) or
   NOT READY TO CLOSE (if certainty is required); final call and the close
   action itself are the Founder's.
6. **AllTrue GitGuardian 3-secret cluster** — confirm whether the
   2026-07-17 alerts (Telegram, APP_KEY, Bearer) duplicate the
   already-rotated SEC-ALLTRUE-001 set or represent a new exposure.
7. **Sunrise Vercel production-deployment cap** (escalated) — confirm
   current capacity status directly via Vercel dashboard/API (not yet done
   this pass); decide whether to open a dedicated GitHub issue since #211
   does not cover this.
8. **Sunrise #211 execution** — decide whether to greenlight execution of
   the already-made FD-1…FD-6 decisions (RLS, rate limiting, backup
   posture) as the next `execute`-mode work, given fail-open rate limiting
   is confirmed live in production now.
9. **Sunrise `chore/dependabot-major-policy` branch** — confirm whether
   this branch (uncommitted wildcard dependabot change, content already
   matches merged PR #249) is stale/redundant or represents in-progress
   intent that should continue.
10. ~~portfolio-ops remote~~ — **RESOLVED this pass**: private repo
    created, branches pushed, Draft PR #1 open.
11. **portfolio-ops Draft PR #1** — review and decide when/whether to
    merge (this session will not merge it).

## Next Highest-ROI Actions (max 5, portfolio-wide)

1. Founder confirms AllTrue #1401 production deploy and executes the
   containment checklist — highest-stakes, PII-of-minors, currently
   entirely unactioned.
2. Founder (or an ops-side check) confirms AllTrue DB-password non-reuse
   (Decision 3) — the single remaining blocker to closing #1387 cleanly —
   and decides on the Actions-log residual risk (Decision 4).
3. Direct Vercel dashboard/API check for Sunrise capacity status, followed
   by a Founder go-ahead to execute Sunrise #211's already-decided items
   (RLS, rate limiting, backup posture) via `execute` mode.
4. Log-level triage of Sunrise's Agent Session Provenance CI failures on
   PR #253 to classify as CI bug vs. real policy violation, and resolve
   the GitGuardian dedup question (Decision 6).
5. Review portfolio-ops Draft PR #1 and decide on the
   `chore/dependabot-major-policy` branch — both low-effort administrative
   items now that the higher-stakes containment work is done.
