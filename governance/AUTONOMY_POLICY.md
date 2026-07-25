# Autonomy policy

**Superseded 2026-07-25.** This file previously granted agents autonomous
merge, deploy, production-data mutation, Gmail deletion, and Git-history
rewrite authority. That grant is revoked. The table below is the current
policy and is authoritative; see `docs/security-boundaries.md` for the full
rationale and `CLAUDE.md` for the always-in-context summary.

## Default posture

Agents act autonomously on read, analysis, triage, and Draft-PR-stage work.
Anything that mutates a shared, external, or production-facing system beyond
a Draft PR requires explicit Founder approval in the session, given at the
time of the action — a past approval for one action does not carry forward to
a similar one.

| Capability | Autonomous | Required control |
|---|---:|---|
| Read GitHub, Gmail, repositories, logs, telemetry | Yes | Minimize PII and secret exposure |
| Triage, label, and organize (non-destructively) | Yes | Never close an issue, never archive/delete Gmail |
| Create/update issues, PR comments, Draft PRs | Yes | Exact target, grounded evidence, marked Draft |
| Send email, reply, or any Gmail mutation | **No** | Founder sends it, or explicitly approves content first |
| Merge a pull request | **No** | Founder merges |
| Deploy to production | **No** | Founder deploys or explicitly directs the deploy step |
| Production data mutation | **No** | Founder approves scope, backup, and executes or explicitly directs it |
| Production verification (read-only checks) | Yes | Read-only: health/version endpoints, logs, dashboards |
| Credential rotation/revocation | **No** | Founder-directed; agents never print secret values |
| Gmail deletion/archival | **No** | Read/search/label-for-review only |
| Git history rewrite | **No** | Founder-directed only, with backup first |
| Close a GitHub issue | **No** | Founder closes, or explicitly approves the close |

## Stop-the-line conditions

Surface immediately (do not wait for the next report cycle) when any of the
following is observed:

- a live or potentially live credential in public history or logs
- production PII or a database dump reachable from published refs
- active data loss, auth bypass, cross-tenant exposure, or financial
  corruption
- a failed backup/restore chain with no verified recovery point
- production identity differing from the intended release

Investigating and documenting the incident is autonomous (read-only evidence
gathering, containment recommendations). Any mutating containment step
(rotating a credential, changing repository visibility, reverting a deploy)
still needs Founder approval unless the Founder has pre-approved that
specific action for that specific incident in this session.

## Gmail

Read and search freely. Label only in ways that aid triage (e.g. a review
queue label) and that do not remove mail from the Founder's normal view.
Never send, reply, delete, archive, or apply a label that hides mail from the
inbox without being asked. Draft replies may be prepared for Founder review
but never sent autonomously.
