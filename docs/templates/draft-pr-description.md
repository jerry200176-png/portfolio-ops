# Draft PR description — template

Every PR opened by an agent is a Draft PR and uses this shape. Never merge
it — that's a Founder decision (`governance/AUTONOMY_POLICY.md`).

```markdown
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
