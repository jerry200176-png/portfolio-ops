# Inventory checklist

## Local repositories

Scan `/home/jerry/workspace` at reasonable depth for Git repositories.
Delegate this to `portfolio-auditor` (read-only). For each repo record:

- name, local path, remote URL, owner, default branch, current branch
- latest commit, commit count last 30d, commit count last 30d by the Founder
- working-tree status, ahead/behind, stash, untracked/uncommitted WIP
- whether it's a duplicate clone, runner checkout, mirror, fork, archive, or
  a real development directory (check `portfolio.yaml.forbidden_checkouts`
  for known-forbidden duplicates before treating a new one as canonical)
- language/framework/database, package manager, deploy target
- production status; presence of README, CLAUDE.md/AGENTS.md, CI, tests,
  deployment workflow

Never merge, move, or delete a folder just because its name looks similar to
another. Flag ambiguity in the report instead.

## GitHub repositories

Delegate to `github-triage` (read-only). Classify:

- **Active 30d**: Founder commit/PR/issue activity in last 30 days, OR CI/
  deployment/production activity in last 30 days, OR no recent commits but
  an open P0/P1, production incident, real user report, or important
  unfinished work.
- **Maintained**: activity in the last 31–90 days, or clear ongoing business/
  product value.
- **Dormant**: no substantial activity in 90+ days and no production/
  open-important work.
- **Reference/Archive**: fork, tutorial, one-off experiment, third-party
  mirror, or already archived.

Recent-30d commit count is a signal, not the sole criterion — an incident-
carrying dormant-looking repo is still Active.

## Cloning missing active repos

Only clone a GitHub repo that is Active-30d or production-critical AND not
already present locally under a path in `portfolio.yaml`. Before cloning:

1. Confirm it isn't the same repo under a different remote/old clone.
2. Clone to `/home/jerry/workspace/<repo-name>` — never overwrite an
   existing directory.
3. Never bulk-clone starred repositories.
4. After cloning, run a baseline audit (`checklists/baseline-audit.md`)
   before making any changes — don't touch it heavily on first contact.

## Writing results

The dispatching mode (not the read-only sub-agent) writes:
`reports/YYYY-MM-DD/portfolio-inventory.md`, and updates `portfolio.yaml`
entries (add missing projects, correct stale fields, flag entries whose
`local_path` no longer exists).
