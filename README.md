# Portfolio Ops

Portfolio Ops holds company governance, evidence and project discovery;
product code stays in its owning repository.

## Start here

1. [`governance/RULEBOOK.md`](governance/RULEBOOK.md), then [`AGENTS.md`](AGENTS.md).
2. [`.claude/skills/portfolio-maintain/SKILL.md`](.claude/skills/portfolio-maintain/SKILL.md)
   and the relevant mode, limited to the task's authorized scope.
3. [`portfolio.yaml`](portfolio.yaml), [`CEO_DASHBOARD.md`](CEO_DASHBOARD.md) and
   [`state/work-queue.yaml`](state/work-queue.yaml). Check each observation's date
   and scope; historical queue entries are not current product acceptance.
4. [`PORTFOLIO.md`](PORTFOLIO.md) for product descriptions and
   [`reference-repositories.yaml`](reference-repositories.yaml) for dated references.

The latest bounded refresh is in
[`reports/2026-10-24/portfolio-reference-refresh.md`](reports/2026-10-24/portfolio-reference-refresh.md).
It separates public GitHub metadata, public runtime identity/health, source-code
facts and unverified workstation/private-project information.

## Current working model

Follow RULEBOOK section 9: a cloud session uses a fresh clone of the owning
repository, a branch from its current default branch, then a PR. Use the actual
session checkout; no fixed `/home/jerry` path is a cloud checkout location.
`CLAUDE.md` is the tool adapter; RULEBOOK owns authorization and machine bans.

| Location or procedure | Meaning |
|---|---|
| Current session checkout | The fresh clone for this task; keep one repository and one task branch |
| `portfolio.yaml` `local_path` fields | Historical workstation discovery records; not instructions to write there |
| `workspace.manifest.yaml` | Retained legacy local layout; not the cloud launch contract |
| `agent-control/`, `docs/workspace-entrypoints/`, ExoProtocol | Retired local gateway/provenance material; never required for cloud work |
| AllTrue legacy and duplicate checkouts | Existing no-edit boundaries remain; no folder is moved, deleted or reclassified here |

See [`docs/workspace-operating-model.md`](docs/workspace-operating-model.md).
Do not install or reactivate the retained gateway merely because its source or
installer remains in this repository. Older local-only procedure steps yield
to RULEBOOK section 9; PR #138 separately addresses checklist portability.

## Maintenance modes

`/portfolio-maintain <mode>` supports `bootstrap`, `triage`, `execute`, `status`
and `weekly-review`. Use `status` for read-only inspection; a documentation
refresh does not authorize Gmail access, a workspace-wide scan, cleanup or
product implementation. Read the selected mode and apply the existing rules.

## Existing read-only checks

```bash
python scripts/check-production-identity.py --json-out <evidence-file>
python scripts/portfolio-freshness.py --fail-on-stale
python scripts/validate-governance-contract.py
python scripts/validate-company-agent-contract.py
python scripts/company-context.py --check
```

The identity probe reads the recorded public health/version endpoints. A
healthy response plus a serving SHA establishes only that observation; it
does not establish product acceptance or equality with GitHub main.

The retained workspace inventory/backup/proposal helpers are for an explicitly
scoped local investigation. `prunable`, an old path, or an old timestamp never
authorizes moving or deleting a worktree. GitHub governance reports are under
[`docs/github-governance/`](docs/github-governance/README.md).

## Delivery evidence

Follow RULEBOOK D0–D9 and [`docs/fleet-merge-policy.md`](docs/fleet-merge-policy.md).
Keep scope, exact-head checks, independent review, rollback and unknowns in the
PR. Use dated evidence in the existing inventory/dashboard; never refresh a
date to imply an unperformed production or workstation verification. This
documentation refresh adds no schedule, permission, installation or activation.
