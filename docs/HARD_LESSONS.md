# Hard lessons (fleet)

One-line rules promoted from repeated or high-risk failures. Product defects
belong in that product's `docs/AI_REGRESSION_LESSONS.md`. This file is for
**control-plane / agent-loop** mistakes.

Format:

```text
- Do not X in Y (seen, see reports/YYYY-MM-DD-….md)
```

Cap at **12** lines. When over cap, drop the oldest that has not recurred;
the original report stays.

## Promotion (any one is enough)

1. The same class of failure appears in learning records **twice or more**.
2. The failure is high-risk or irreversible.
3. The Founder says to remember it.

Agents may **append** a matching one-liner here. They must not edit other
governance files to promote a lesson, and must not delete Founder-authored
lines.

## Current list

- Same step failed twice, or stalled five minutes: stop and ask; do not keep
  retrying in silence (see `docs/agent-operating-loop.md`).
- On 收工, write technical record and public journal separately; do not mix
  them (see `docs/session-closeout.md`).
