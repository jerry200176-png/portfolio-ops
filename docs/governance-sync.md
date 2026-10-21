# Governance sync and new projects

How the portfolio rulebook reaches every repo, so one edit in portfolio-ops updates all of them.
Rules live in `governance/RULEBOOK.md`; this file is the how-to.

## Flow

1. Edit `governance/RULEBOOK.md` (or the vendored skills, `scripts/check-rulebook.py`, the PR
   template) in a portfolio-ops PR. Update `rules.yaml`, the lock `sha256` and `DECISIONS.md`.
2. On push to `main`, `.github/workflows/rulebook-sync.yml` runs `scripts/sync-governance.py`.
   For each project in `portfolio.yaml` with `governance_sync: true` it opens a PR
   `chore/rulebook-sync-<sha7>` that re-vendors the rulebook (through the target's own
   `check-rulebook.py --update`, so the lock hash stays right), the script and the skills, and
   closes older sync PRs. The PR template is copied only when missing; if it lacks the
   參考做法 / 設計文件 / 重複檢查 sections the PR says so.
3. Sync PRs are R0 byte copies of already-reviewed text. The bot queues `gh pr merge --auto
   --squash`; the target merges when its required CI is green. Repos without auto-merge enabled
   get a normal PR for the land queue.

Why not BetaHuhn/repo-file-sync-action: it copies files verbatim and cannot rewrite the lock
hash per repo, and it adds a third-party action holding a write token (rulebook B10). The script
is the same one-way, one-commit sync pattern as Copybara, in about 120 lines of stdlib Python.

## Founder one-time setup

Create a fine-grained personal access token and store it as the portfolio-ops Actions secret
`GOVERNANCE_SYNC_TOKEN`. Resource owner `jerry200176-png`; repositories: only the repos with
`governance_sync: true`; permissions: Contents read/write, Pull requests read/write, Metadata
read. No workflow, admin or secrets permission. Expires in 90 days; renew before expiry.
Until it exists the workflow prints a notice and skips. Agents never create secrets.

## Reusable CI

Product repos call the check with one job (see `governance/templates/rulebook-check-caller.yml`):

```yaml
jobs:
  rulebook:
    uses: jerry200176-png/portfolio-ops/.github/workflows/rulebook-check.yml@<portfolio-ops sha>
```

## Add a project

```bash
scripts/bootstrap-repo.sh owner/new-repo        # branch chore/governance-bootstrap in the target
```

It writes the AGENTS.md skeleton (digest + TODO sections), CLAUDE.md imports, the vendored
rulebook and lock, skills, PR template and the CI caller, then registers the repo in
`portfolio.yaml` (`governance_sync: true`). Open the printed PR in the target and commit the
`portfolio.yaml` change in portfolio-ops. Fill the AGENTS.md TODOs (commands, domain red lines).
Retired repos (for example exoprotocol) stay `governance_sync: false`.
