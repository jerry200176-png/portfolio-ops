# Strong Plan → implementation handoff

Copy into the product’s existing plan/delivery path (AllTrue:
`*_EXECUTION_PLAN.md` / delivery artifacts). One Plan revision per handoff.
Do not invent a second plan schema.

## Header

- Plan ref / revision:
- Goal / signal id(s):
- Planning Lead role + requested tier (`sol` / `astra`):
- Model evidence: requested · resolved config · tool-reported actual · or `UNKNOWN`
- CLI / config versions:
- Fallback / quota / error (if any):
- Authorization basis (existing auto-fix envelope / visible Founder GO / other):
- Implementation profile (approved light worker only):

## Problem & root-cause evidence

- User problem / expected behavior:
- Root-cause evidence (code, tests, runtime) with paths:
- Hypotheses still open:

## Goals / non-goals

- In scope:
- Out of scope:

## Nine facets (N/A + reason allowed)

| Facet | Answer or N/A + reason |
|---|---|
| Product & execution | |
| Architecture | |
| Platform & infrastructure | |
| Delivery & release | |
| Production reliability | |
| Observability | |
| Security | |
| Governance | |
| Agent productivity / routing | |

## Contracts & invariants

- Files / APIs / versions in play:
- Invariants the worker must not change:
- Acceptance criteria (testable):
- Dependencies / tools / data prerequisites:

## Release & recovery

- Slice / verification commands:
- Rollback / stop conditions (within existing authority):

## Deviation routing

- Ordinary engineering / CI drift → Planning Lead
- New product meaning or protected decision → Founder
- Retry / cost bound:
- Stop reason if no progress:

## Worker return

- Diff / head:
- Tests run + results:
- Reviewer note (independent of approver role):
- Open questions for Lead:
