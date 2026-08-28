# Autonomous governance for a one-person company

The operating model is agent-first: recurring work should run without asking
the Founder to inspect every repository. Human involvement is reserved for
actions that can destroy, publish, merge, deploy, or change production state.

## Autonomy boundary

| Tier | Agent does automatically | Founder decision |
| --- | --- | --- |
| Observe | discover Git roots, read status, compare contracts, refresh evidence | none |
| Verify | validate inventory shape, governance policy, tests, and report freshness | none |
| Organize | classify clean/dirty/unresolved state and clean only controller-owned runtime files | none, when the ownership marker and policy match |
| Escalate | create an exception queue with path, risk, owner, recovery, and next step | decide keep, archive, remove, move, or other lifecycle action |
| Never delegate | reset, clean, rebase, force-push, credential or Gmail mutation | Founder-directed process only |

The machine-readable policy is
`governance/autonomy-automation.yaml`. The implementation is
`scripts/governance-autopilot.sh`.

## Run it

First produce an inventory with the existing read-only inventory command, then
pass that evidence to the autopilot:

```bash
scripts/workspace-inventory.sh /tmp/portfolio-inventory.tsv \
  /home/jerry/workspace /home/jerry/wt /home/jerry
scripts/governance-autopilot.sh \
  --policy governance/autonomy-automation.yaml \
  --inventory /tmp/portfolio-inventory.tsv \
  --output /home/jerry/evidence/workspace-admin/governance-autopilot.json
```

The default invocation writes evidence only. It does not touch a checkout.
`--apply-safe-cleanup` is deliberately narrower: it only sends files matching
the policy patterns to the desktop Trash when the exact policy runtime root
contains `.governance-autopilot-owned`. A missing marker means no cleanup.
Every report also records SHA-256 digests for the policy and source inventory,
so a later reviewer can prove which inputs produced the exception queue.

## Completion signal

An unattended run is healthy when the report is written, the inventory has no
malformed rows, and the approval queue is either empty or contains explicit
owner decisions. Dirty or unresolved paths are not failures to hide; they are
durable exceptions that remain recoverable until ownership is known.

This makes the workflow scalable for one person while preserving the control
that mature companies place around irreversible changes: automation handles
the high-volume observation and verification, and the Founder only decides
the small number of actions with material recovery or business impact.
