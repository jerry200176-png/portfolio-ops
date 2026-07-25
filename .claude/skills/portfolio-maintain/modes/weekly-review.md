# Mode: weekly-review

Everything in `triage.md`, plus a wider sweep. Run at most weekly — this is
not the default daily mode.

## Additional steps beyond triage

1. Security posture: recent secret-scanning/Dependabot alerts across Tier
   0/1 repos, via `security-reviewer` (read-only).
2. Dependency health: outdated/vulnerable dependencies, without proposing a
   bulk upgrade (`../../../docs/prioritization.md` — first-round exclusion
   still applies unless a dependency is an active security risk).
3. Delivery signals: recent CI pass rate, deploy frequency/failure rate per
   Tier 0/1 project, from GitHub data already gathered in triage.
4. Product KPI trends: only if a real signal source exists (production
   telemetry, prior reports) — do not fabricate metrics.
5. Governance drift: check whether `governance/AUTONOMY_POLICY.md`,
   `CLAUDE.md`, and actual recent agent behavior (per `state/work-queue.yaml`
   evidence) still agree. Flag drift, don't silently "fix" policy files
   without surfacing the change.
6. Stale work: `reports/`/`state/work-queue.yaml` items untouched 30+ days
   with no Tier 0/1 justification — propose archival, don't archive
   unilaterally (archival of Issues/branches needs Founder approval per
   `../../../CLAUDE.md`).
7. Optionally run `checklists/reference-repos.md` for any Tier 0/1 project
   whose baseline audit surfaced an unresolved architecture question.

## Output

`reports/YYYY-MM-DD/weekly-review.md` plus the same `CEO_DASHBOARD.md`
refresh as `triage`.
