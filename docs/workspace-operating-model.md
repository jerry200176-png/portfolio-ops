# Workspace operating model

## Current default: cloud session

RULEBOOK section 9 is authoritative: fresh clone of the owning repository,
branch from its current default branch, PR. The actual checkout path belongs
to that session; do not guess a `/home/jerry` path or require a local launcher,
preflight, Exo tree or local session manifest. The PR's branch, diff, review
and exact-head checks are the cloud session's delivery record.

This is a correction of the existing rule, not a new permission or installer.
Product instructions still supply domain safety rules and required checks.

## Historical workstation layout

`workspace.manifest.yaml` and the `local_path` entries in `portfolio.yaml`
retain the earlier local discovery layout. Those paths were not inspected
on the Founder's workstation in the 2026-10-24 documentation refresh.

| Retained local area | Historical purpose |
|---|---|
| `repos/` | Bare Git object stores, not app-code edit directories |
| Product and duplicate checkouts | Previously discovered checkouts; keep their existing no-edit boundaries |
| `tasks/`, `worktrees/` | Legacy local task directories, not mandatory cloud roots |
| `archives/`, `evidence/`, `backups/` | Preserved state/recovery records; existence or age does not authorize deletion |
| `agent-control/`, `docs/workspace-entrypoints/` | Retired local launch/preflight sources |

Do not run retained installers or move/reclassify a checkout to make the old
layout appear current. A missing local directory is UNKNOWN when the local
machine was not examined. Never overwrite user work or infer permission from
`prunable` metadata. Any local recovery/integration task needs its own bounded
inventory, recovery evidence and the existing applicable authorization.

## Owning repositories

Portfolio Ops records metadata, evidence and governance; product source stays
in the product repository. Existing `catalog/` files remain the component
descriptors. This refresh does not edit their runtime/control contracts or
deploy anything. Public repository heads, public serving SHAs and product
acceptance are separate observations; see the dated refresh report.
