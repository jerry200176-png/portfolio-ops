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

## Activation and migration

`/portfolio-maintain bootstrap`, `status`, `triage`, `execute`, and
`weekly-review` remain unchanged. Triage may propose one bounded mission;
`/portfolio-run` never selects a different project or performs broad triage.
Create the mission with the `create` command in the Skill, complete its contract
and steps, validate, then run it. Use `active`, `next`, and `approvals` for the
operator view; use `checkpoint` on a safe stop and `resume` in a new session.

Founder-only actions are queued once per bundle key while unrelated preparation
continues. Pending CI is monitored, not treated as completion. A mission closes
only after its recorded exit criteria pass. Return to `/portfolio-maintain
triage` after closing it. For an emergency stop, checkpoint with
`safety_boundary`; rollback by reverting only the mission-state change or the
PR that introduced the harness. To remove the harness cleanly, revert its PR;
do not alter existing hooks, policy, work queue, or Dashboard.

## Claude-only smoke test

Codex cannot demonstrate Claude Code slash-command discovery. In a fresh Claude
Code session, invoke `/portfolio-run` and confirm its description is offered;
create a synthetic mission, run `validate`, `run`, `next`, `approvals`, and
`resume` with `--writer claude_code`, then confirm `/portfolio-maintain status`
still performs its documented read-only status flow. Record that evidence in the
mission/report before activating on real work.
