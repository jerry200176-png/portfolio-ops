# PR description — template

Every agent PR uses this shape. After required GitHub checks are green,
squash-merge R0–R3 (`docs/fleet-merge-policy.md`). Do not `--admin`. The
Agent is the operator; do not wait for a Founder click.

```markdown
## Risk-Class
R0 | R1 | R2 | R3

## Evidence
<What was observed, where, and how — link issues/logs/production evidence.>

## Root cause
<The mechanism, not just the symptom.>

## Changes
<What this PR does, minimally scoped to the root cause.>

## Tests
<What was run, in this session, with results. State plainly if CI couldn't
run and why.>

## Risk
<Blast radius if this is wrong; what it touches in production.>

## Rollback
<Concrete steps to revert if this causes a problem post-merge.>

## Unverified
<Anything not confirmed — be explicit rather than silent.>
```
