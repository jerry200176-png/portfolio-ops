# Autonomy policy

**Revised 2026-08-15.** This file is the **fleet** capability table for every
governed repository. Product overlays add domain P0 bans and extra CI
checks; they do not re-ban merge after required checks pass.

The 2026-07-25 blanket “agents never merge” rule is withdrawn. Founder
decision: a human click that does not re-derive CI is not a control.
Procedure: `docs/fleet-merge-policy.md`. Rationale: `docs/security-boundaries.md`.

## Default posture

Agents implement on a branch, open a PR, wait for **required** GitHub
checks, then squash-merge. Deploy workflows that run *because* `main`
advanced are allowed as a consequence of that merge. Anything that mutates
production **outside** that path still needs Founder approval in the
session.

| Capability | Autonomous | Required control |
|---|---:|---|
| Read GitHub, Gmail, repositories, logs, telemetry | Yes | Minimize PII and secret exposure |
| Triage, label, and organize (non-destructively) | Yes | Never close an issue, never archive/delete Gmail |
| Create/update issues, PR comments, PRs | Yes | Exact target, grounded evidence |
| Merge a pull request (R0–R2) | **Yes** | Required checks green; no `--admin`; `docs/fleet-merge-policy.md` |
| Merge a pull request (R3) | **No** | Founder; Repair Manifest / execution gate |
| Send email, reply, or any Gmail mutation | **No** | Founder sends it, or explicitly approves content first |
| Deploy outside default-branch product workflow | **No** | Founder; product control plane only |
| Production data mutation / Repair Manifest execute | **No** | Founder approves scope, backup, and executes or directs it |
| Production verification (read-only checks) | Yes | Read-only: health/version endpoints, logs, dashboards |
| Credential rotation/revocation | **No** | Founder-directed; agents never print secret values |
| Gmail deletion/archival | **No** | Read/search/label-for-review only |
| Git history rewrite / force-push | **No** | Founder-directed only, with backup first |
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
(rotating a credential, changing repository visibility, reverting a deploy
outside the product workflow) still needs Founder approval unless the
Founder has pre-approved that specific action for that specific incident in
this session.

## Gmail

Read and search freely. Label only in ways that aid triage (e.g. a review
queue label) and that do not remove mail from the Founder's normal view.
Never send, reply, delete, archive, or apply a label that hides mail from
the inbox without being asked. Draft replies may be prepared for Founder
review but never sent autonomously.
