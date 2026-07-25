# Portfolio Mission Loop Harness

`/portfolio-run` runs one bounded, resumable control-plane mission. Durable
state is `state/missions/`, never chat history. The included runner takes
JSON-compatible YAML and adds no dependencies.

Use `/portfolio-maintain` for discovery, triage, status, and weekly review;
then create a mission contract and use `/portfolio-run` for the selected work.
Do not alter `state/work-queue.yaml` or the active Claude mission to migrate.

Draft PRs, reports, and pending CI are progress, not stop conditions. Monitor
pending external state; retry a repair once; queue bundled Founder-only actions
while independent documentation and verification work continues. The state
schema permits only the five explicit terminal reasons.

One executor writes state. An optional fresh-context verifier is read-only,
cannot edit product code or recurse, and each finding is recorded with an
adopted/rejected/deferred disposition. Existing `CLAUDE.md`, governance,
hooks, deny rules, Git restrictions, and production-data boundaries remain the
only safety authority; this harness neither weakens nor duplicates them.
