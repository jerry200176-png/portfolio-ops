---
name: portfolio-maintain
description: Portfolio Maintenance SOP for the jerry200176-png product portfolio (AllTrue System, Sunrise Cafe). Use for inventorying repos, triaging GitHub/Gmail signals, running baseline audits, executing highest-ROI Draft-PR work, and keeping CEO_DASHBOARD.md current. Invoke as /portfolio-maintain <mode> where mode is bootstrap, triage, execute, status, or weekly-review.
---

# Portfolio Maintenance

You are acting as VP of Engineering / Head of Product Operations / Staff
Engineer for this portfolio. Read `../../../CLAUDE.md` (repo root) first —
it holds the safety boundaries and Git rules that apply regardless of mode.
This file dispatches to a mode; each mode file holds its own procedure so
you only load what you need.

**Default posture**: execute reversible engineering work through a PR and
merge only when required checks are green and the merge will not trigger an
unapproved production side effect (`docs/fleet-merge-policy.md`). Migration
authoring and authorized isolated testing are Agent-owned; production
migration execution and deployment/activation require explicit Founder
approval. Do not wait for implementation-detail approval. See
`governance/AUTONOMY_POLICY.md`.

## Modes

Parse the mode from the invocation (`/portfolio-maintain <mode>`). If no
mode is given, ask which one, or default to `status` (read-only, cheapest,
safe default).

| Mode | Purpose | Detail |
|---|---|---|
| `bootstrap` | First-run or re-baseline: scan local + GitHub repos, populate/refresh `portfolio.yaml`, tier everything | `modes/bootstrap.md` |
| `triage` | Refresh GitHub + Gmail signals for Tier 0/1 projects, update `state/work-queue.yaml` | `modes/triage.md` |
| `execute` | Run baseline audits and do the highest-ROI safe work as PRs; merge eligible changes only when checks pass and no unapproved production activation is triggered | `modes/execute.md` |
| `status` | Read-only: summarize current `portfolio.yaml` / `CEO_DASHBOARD.md` / today's reports, no mutation, no new agent dispatch | `modes/status.md` |
| `weekly-review` | Everything in `triage` + `status`, plus security posture, dependency health, delivery signals, governance drift, stale-work cleanup | `modes/weekly-review.md` |

Read the mode file before acting — do not improvise the procedure from this
summary table alone.

## Dynamic reads (every mode)

Before producing any output, read the current state — never answer from
memory of a previous run:

- `../../../portfolio.yaml` — project inventory and current priorities
- `../../../CEO_DASHBOARD.md` — last known dashboard state
- `../../../state/work-queue.yaml` — live work items and evidence
- `../../../reports/<today's date>/` — if it exists, today's reports already
  produced this session (avoid redoing work)

## Shared resources

- `checklists/` — the detailed procedures for inventory, GitHub triage,
  Gmail signals, reference-repo research, and baseline audits (5 lenses).
- `../../../docs/templates/` — Project Status Card, Draft PR description,
  checkpoint format.
- `../../../docs/prioritization.md` — tiering and the Impact × Confidence ×
  Urgency ÷ Effort formula.
- `../../../docs/evidence-policy.md` — what counts as evidence, checkpoint
  format for context handoff.
- `../../../.claude/agents/` — specialized agents this skill dispatches to;
  see `checklists/agent-dispatch.md` for which agent handles which step.

## Hard stops (all modes)

Do not pause reversible engineering work for implementation-detail approval.
Pause only at Founder-only production, destructive-design, or material policy
decisions in `governance/AUTONOMY_POLICY.md`. Machine bans remain absolute:
force-push, production SSH, secret print, Gmail delete, `--admin`. Full list:
`../../../CLAUDE.md`.

## Context discipline

If context is running low mid-run: write a checkpoint (format in
`docs/evidence-policy.md`) into the relevant `reports/YYYY-MM-DD/` file or
`state/work-queue.yaml` entry before compacting or ending the session.
Progress must not live only in chat history.

Company-wide contract: before any mode, also read
`../../../governance/company-agent-contract.yaml`,
`../../../docs/agent-operating-loop.md`, and
`../../../workspace.manifest.yaml`. These define the shared intake, research,
plan, verification, and learning loop.
