# Gmail Signals — 2026-07-25

Read-only. Delegated to `gmail-signal-analyst` (AllTrue, Sunrise) — search
and read only, no drafts/sends/labels. Summaries only; no full email bodies
or unnecessary PII copied in, per `checklists/gmail-signals.md`. Every
signal below is cross-checked against the GitHub-triage findings in
`github-triage.md` where possible before being treated as evidence
(`docs/evidence-policy.md`).

## AllTrue System

| Date | Signal type | Summary | Severity | GitHub issue exists? | Next step |
|---|---|---|---|---|---|
| 2026-07-17 | GitGuardian alert (x3) | Telegram Bot Token, Laravel APP_KEY, and a Bearer Token flagged as exposed in AllTrue_System | High (unverified whether duplicate of already-rotated SEC-ALLTRUE-001 set) | Unconfirmed — Gmail agent has no GitHub tool access to check | Cross-checked in `github-triage.md` #2: status is "unresolved-pending-confirmation," needs direct secret-scanning pull to dedupe against SEC-ALLTRUE-001 closure evidence |
| ~2026-07-24 | Incident/parent-portal report | Signal consistent with the cross-student exposure later tracked as issue #1401 | High | Yes — issue #1401 exists (confirmed via GitHub triage) | See `github-triage.md` #1 — containment checklist unexecuted, Founder decision needed |

Note: the Gmail agent could not independently confirm whether GitHub issues
already existed for these signals (no GitHub tool access). Both have now
been cross-checked against the GitHub-triage pass above — the GitGuardian
cluster is *not yet resolved to a specific issue/PR*, while the
parent-portal signal *does* map to an existing issue (#1401).

## Sunrise Cafe

| Date | Signal type | Summary | Severity | GitHub issue exists? | Next step |
|---|---|---|---|---|---|
| multiple (recent) | Vercel deployment-cap failure | "Resource is limited - try again in 24 hours" — now confirmed hitting **production** deploys directly on multiple dates, not only preview | High (escalated from prior assessment) | No — GitHub triage confirmed issue #211 is about Supabase RLS/rate-limit/backup decisions, not Vercel capacity; this is an uncovered gap | Open as new work-queue item (`OPS-SUNRISE-001` evidence updated below); needs direct Vercel dashboard/API check, not yet performed |
| recurring (≥8x / 30 days) | CI failure pattern | Agent Session Provenance check failing repeatedly | Medium-High (governance gate, not confirmed production-impacting) | Yes — confirmed as a real failing required check on PR #253 by GitHub triage | See `github-triage.md` #1 — needs log-level triage to classify as CI bug vs. real policy violation |

## Cross-verification outcome

- **AllTrue GitGuardian cluster**: elevated from "signal only" to
  "candidate P0, pending confirmation" — do not treat as already-resolved
  under SEC-ALLTRUE-001 without direct secret-scanning confirmation.
- **AllTrue parent-portal signal**: confirmed mapped to issue #1401; Gmail
  signal alone would not have justified action, but the GitHub-side
  evidence (merged fix PR #1400, unchecked containment checklist)
  independently supports treating this as the top portfolio item this pass.
- **Sunrise Vercel cap**: confirmed as a real gap with no corresponding
  GitHub issue — this is a genuine blind spot in the current work queue,
  now being added as its own line item rather than folded into #211.
- **Sunrise Agent Session Provenance**: Gmail pattern (recurrence count)
  corroborated by GitHub triage (actual failing check observed on a real
  PR) — mutually reinforcing, elevated to a tracked item.
