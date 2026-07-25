---
name: portfolio-run
description: Run or resume one bounded Portfolio Mission Loop from durable state. Use for a mission goal that must continue through Observe, Plan, Act, Verify, checkpointing, pending CI monitoring, and Founder-only approvals without treating intermediate PRs or pending CI as completion.
---

# Portfolio Mission Loop

Read `../../../CLAUDE.md` first. Claude Code remains the production controller
and primary executor. This control-plane harness records intent, evidence,
approvals, and checkpoints; it grants no authority beyond existing policy.

Use `/portfolio-run run <mission-id>` or `/portfolio-run resume <mission-id>`.
The source of truth is `state/missions/<mission-id>.yaml`, not chat history.
Validate the outcome contract and run:

```sh
python3 .claude/skills/portfolio-run/scripts/mission_loop.py run --mission state/missions/<mission-id>.yaml
```

The runner reads JSON-compatible YAML without added dependencies. Claude
performs real authorized Observe → Plan → Act → Verify work and records it.
An opened Draft PR is evidence, not completion. Monitor pending external state
and continue other unblocked work. Repair an actionable failure and retry once.
Queue and bundle related Founder-only actions; stop for `founder_only_blocker`
only when no safe work remains. Allowed terminal reasons only:
`mission_complete`, `founder_only_blocker`, `safety_boundary`,
`tool_unavailable`, `budget_or_turn_cap`.

Use one executor and optionally one fresh-context read-only verifier. The
verifier cannot edit product code or recursively dispatch reviewers. Record
every finding in `verification.reviewer_findings` with `adopted`, `rejected`,
or `deferred` disposition and rationale.

On resume, read durable state, approval queue, and policy; verify repository
reality; preserve completed work; then continue `next_action`. Never recreate a
PR in `evidence.opened_prs`. Keep detailed output in state/report files and
final output within the policy limit. Preserve existing hooks, deny rules,
destructive-Git restrictions, production boundaries, and read-only limits.
