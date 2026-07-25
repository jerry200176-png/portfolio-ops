# Mode: status

Pure read, no mutation, no sub-agent dispatch. Cheapest mode; safe default
and safe for `--dry-run`-style checks.

## Steps

1. Read `../../../portfolio.yaml`, `../../../CEO_DASHBOARD.md`,
   `../../../state/work-queue.yaml`.
2. Read today's `../../../reports/<YYYY-MM-DD>/` if present.
3. Summarize to the Founder: portfolio table as currently recorded, open
   P0/P1 counts, current priority per Tier 0/1 project, decisions required,
   and how stale each figure is (compare `updated_at`/`latest_activity`
   against today's date — flag anything not refreshed this week).
4. If asked to "run status" as a dry run: perform steps 1–3 only, write
   nothing, mutate nothing, and end by naming what a real `triage` or
   `execute` run would do next.

Do not fetch git remotes, hit production endpoints, or call GitHub/Gmail
tools in this mode — that's `triage`'s job. `status` reports what's already
recorded.
