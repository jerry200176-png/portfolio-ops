---
name: portfolio-run
description: Run or resume one bounded Portfolio Mission Loop from durable state. Use for a mission goal that must continue through Observe, Plan, Act, Verify, checkpointing, pending CI monitoring, and Founder-only approvals without treating intermediate PRs or pending CI as completion.
---

# Portfolio Mission Loop

Read `../../../CLAUDE.md` first. Claude Code remains the production controller
and primary executor. This control-plane harness records intent, evidence,
approvals, and checkpoints; it grants no authority beyond existing policy.

Use `/portfolio-run run --mission state/missions/<mission-id>.yaml` or the
equivalent `resume` command.
The source of truth is `state/missions/<mission-id>.yaml`, not chat history.
Validate the outcome contract and run:

```sh
python3 .claude/skills/portfolio-run/scripts/mission_loop.py run --mission state/missions/<mission-id>.yaml
```

The runner reads JSON-compatible YAML without added dependencies. Claude
performs real authorized Observe → Plan → Act → Verify work and records it.
An opened Draft PR is evidence, not completion. A pending external state creates
a monitor checkpoint (never a stop reason); resume to re-observe it while other
unblocked work continues. Repair an actionable failure and retry once.
Queue and bundle related Founder-only actions; stop for `founder_only_blocker`
only when no safe work remains. Allowed terminal reasons only:
`mission_complete`, `founder_only_blocker`, `safety_boundary`,
`tool_unavailable`, `budget_or_turn_cap`.

Use one executor and optionally one fresh-context read-only verifier. The
verifier cannot edit product code or recursively dispatch reviewers. Record
every finding in `verification.reviewer_findings` with `adopted`, `rejected`,
or `deferred` disposition and rationale.

## Operator commands

Claude Code is the sole writer of active mission state. The required
`--writer claude_code` guard makes that execution role explicit; it is not a
new permission or authority grant. Use the smallest set of commands:

```sh
# create, then fill the outcome contract and bounded steps
python3 .claude/skills/portfolio-run/scripts/mission_loop.py create --writer claude_code --mission-id <id> --title <title> --goal <goal>
python3 .claude/skills/portfolio-run/scripts/mission_loop.py validate --mission state/missions/<id>.yaml
python3 .claude/skills/portfolio-run/scripts/mission_loop.py run --writer claude_code --mission state/missions/<id>.yaml
python3 .claude/skills/portfolio-run/scripts/mission_loop.py next --mission state/missions/<id>.yaml
python3 .claude/skills/portfolio-run/scripts/mission_loop.py approvals
python3 .claude/skills/portfolio-run/scripts/mission_loop.py resume --writer claude_code --mission state/missions/<id>.yaml
```

Use `active` only after triage has created exactly one non-example active
mission. `checkpoint` and `close` are guarded writes; `close` requires recorded
`verification.exit_criteria_passed`. The script deliberately does not invoke
Claude runtime skills itself. Perform the Claude-only smoke test in
`docs/portfolio-run.md` before activation.

On resume, read durable state, approval queue, and policy; verify repository
reality; preserve completed work; then continue `next_action`. Never recreate a
PR in `evidence.opened_prs`. Keep detailed output in state/report files and
final output within the policy limit. Preserve existing hooks, deny rules,
destructive-Git restrictions, production boundaries, and read-only limits.
