# Mode: triage

Refresh signals for Tier 0/1 projects without re-running the full inventory.
Use when `portfolio.yaml` already exists and is roughly current.

## Steps

1. Read `../../../portfolio.yaml`; for each Tier 0/1 project, confirm
   `local_path` still exists and Git state (fetch, check branch/dirty/stash).
2. `checklists/github-triage.md` per Tier 0/1 project.
3. `checklists/gmail-signals.md` per Tier 0/1 project.
4. Read-only production verification: hit each project's `version_url`/
   `health_url` from `portfolio.yaml`, record result.
5. Update `state/work-queue.yaml` (evidence, status, next_action per item)
   and `portfolio.yaml` (`open_p0`, `open_p1`, `current_priority`,
   `next_action`, `latest_activity`).
6. Update `CEO_DASHBOARD.md`'s Portfolio Table and Decisions Required
   sections from fresh evidence — don't leave it citing a prior run's
   numbers.
7. Write `reports/YYYY-MM-DD/github-triage.md` and
   `reports/YYYY-MM-DD/gmail-signals.md` (or append if today's already
   exist).

This mode does not implement anything — it's the input to `execute`.
