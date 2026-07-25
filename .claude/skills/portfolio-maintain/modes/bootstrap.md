# Mode: bootstrap

First run, or a full re-baseline. Produces/refreshes `portfolio.yaml` and
the initial `reports/YYYY-MM-DD/` set.

## Steps

1. `checklists/inventory.md` — local + GitHub repo scan, clone missing
   Active-30d repos if genuinely missing. Write
   `reports/YYYY-MM-DD/portfolio-inventory.md`.
2. Tier every project per `../../../docs/prioritization.md`. Write/update
   `portfolio.yaml` (validate shape against `../../../schemas/portfolio.schema.yaml`).
3. For each Tier 0/1 project: `checklists/github-triage.md`,
   `checklists/gmail-signals.md`.
4. `checklists/reference-repos.md` for Tier 0/1 projects with a concrete
   live problem (skip if none yet identified — don't force it).
5. `checklists/baseline-audit.md` for each Tier 0/1 project, one at a time.
   Produces Project Status Cards.
6. Write `reports/YYYY-MM-DD/maintenance-plan.md`: cross-portfolio top-5
   next actions per `../../../docs/prioritization.md`.
7. Update `CEO_DASHBOARD.md` and `PORTFOLIO.md` (only the narrative parts
   that actually changed).

## Do not

Clone all starred repos, touch `forbidden_checkouts` paths, or start
`execute`-mode implementation work as part of bootstrap — bootstrap ends at
a trustworthy baseline. Run `execute` mode separately once the baseline is
in place.
