# Portfolio Ops

This directory is the portfolio control plane for jerry200176-png's product
portfolio:

- `jerry200176-png/AllTrue_System`
- `jerry200176-png/sunrise-cafe`

AI agents handle read, analysis, triage, and Draft-PR-stage implementation
work autonomously. Merging, deploying, production data mutation, Gmail
mutation, issue closure, credential rotation, and Git history rewrites all
require explicit Founder approval given in the session — see
`governance/AUTONOMY_POLICY.md` and `CLAUDE.md`. (Formerly `company-os`,
which granted broader autonomy; that grant was revoked 2026-07-25 — see
`PORTFOLIO.md`'s change log.)

## Canonical locations

| Purpose | Path |
|---|---|
| Portfolio control plane (this repo) | `~/workspace/portfolio-ops/` |
| Safe agent session launcher | `~/workspace/agent-control/` |
| AllTrue canonical checkout | `~/workspace/AllTrue_System-clean/` |
| Sunrise canonical checkout | `~/workspace/sunrise-cafe/` |
| Legacy AllTrue checkout | `/home/jerry/alltrue` — never edit |

## Start here

1. `CLAUDE.md` — safety boundaries, Git rules, Founder decision boundary.
2. `.claude/skills/portfolio-maintain/SKILL.md` — the operating procedure,
   invoked as `/portfolio-maintain <mode>`.
3. `portfolio.yaml` and `CEO_DASHBOARD.md` — current portfolio state.
4. `PORTFOLIO.md` — narrative overview and change log.
5. `governance/AUTONOMY_POLICY.md` and `governance/COMPANY_CONSTITUTION.md`
   — the full policy behind `CLAUDE.md`'s summary.
6. `governance/repository-governance.yaml` — fleet policy and required agent
   adapters/enforcement.
7. `state/work-queue.yaml` — live work items and evidence.

## Standard launch flow

```bash
cd ~/workspace/portfolio-ops
claude --add-dir ~/workspace
```

Then, inside the session:

```
/portfolio-maintain <mode>      # bootstrap | triage | execute | status | weekly-review
/goal <completion condition>    # optional: state what "done" means for this run
```

Start with `/portfolio-maintain status` (read-only, cheapest) if you just
want current state. Use `bootstrap` only for a first run or a full
re-baseline; use `triage` to refresh signals; use `execute` to do the
highest-ROI safe work as Draft PRs; use `weekly-review` for the wider
weekly sweep.

From Ubuntu, `governance-audit` audits GitHub enforcement without writing.
`governance-onboard owner/repo --dry-run` previews a new project; `--apply`
creates an isolated onboarding worktree with the pinned ExoProtocol governance
core and only missing adapters. After that bootstrap PR merges,
`governance-onboard owner/repo --apply --enable-ci` adds the Exo CI workflow as
a separate reviewable change.

## Definition of done (this control plane's scope)

A portfolio-maintenance task is complete only when: the relevant finding or
change is recorded with evidence (not just claimed), any code change is on
its own branch with a Draft PR opened (never merged by an agent), tests/
lint/build were actually run in-session, `portfolio.yaml` and
`CEO_DASHBOARD.md` reflect the outcome, and anything requiring merge,
deploy, production data mutation, or another item on `CLAUDE.md`'s "never"
list is surfaced to the Founder as a Decision Required rather than done
silently.
