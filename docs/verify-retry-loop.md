# Verify-retry inner loop

This is an inner loop on `implement -> verify` for **eligible** work. It does
not replace `docs/agent-operating-loop.md`, ExoProtocol, or
`governance/AUTONOMY_POLICY.md`. Merge of R0–R2 after required GitHub checks
follows `docs/fleet-merge-policy.md`. Deploy outside the product
default-branch workflow, production data mutation, mail send, credential
changes, and history rewrites stay Founder-gated even when this loop is green.

The maturity idea (spec, independent checker, auto retry, run record) is
adapted from Captain Balung's public map
[遠航七階](https://captain-balung-blog.ghost.io/seven-stages-ai-agent-workflow/).
That article is a map, not a runnable SOP. Do not copy its ceremony, and do
not read "human leaves the loop" as permission to skip GitHub required checks.

## Eligibility

Use this loop only when **all** of the following are true:

1. Risk is T0 docs-only or T1 low-risk code with an existing automated check.
2. Success can be written as commands or file predicates that a second agent
   can re-run without looking at the chat.
3. Failure should retry the implementation, not guess a new architecture.
4. The task is a repeatable class, not a one-off product decision.

Do **not** use it for T2/T3 product, auth, PII, billing, migrations, CI
rewrites, or any irreversible action. If the checker cannot be written as
commands, stay on the outer loop: implement once, human or Founder reviews.

First pilot class: **portfolio-ops T0 docs** (this repository's `docs/` and
templates only, no `.github/` workflow edits unless the task is explicitly
about those files).

## Required artifacts before the first implement pass

Write these in the GitHub plan issue or the session note:

- Spec: in-scope paths, out-of-scope paths, and the user-visible outcome.
- Checks: the exact commands or predicates (see below).
- Stop-loss: max attempts (default **3**) and what happens when exhausted
  (stop, record, do not keep regenerating).
- Retry target: on check failure, retry **implementation** unless the
  independent checker shows the spec or checks themselves are wrong.

## Machine-checkable acceptance

Each check must be a command the implementer and the reviewer can both run.
Examples that count:

```bash
git diff --check
python3 scripts/validate-company-agent-contract.py
python3 -m unittest tests.test_governance_baseline
test -f docs/verify-retry-loop.md
```

Examples that do not count: "reads well", "matches brand", "Founder will
like it", or any check that exists only in the implementer's narrative.

## Generate / review split

- **Implementer** writes the diff and runs the checks.
- **Reviewer** (separate skill/subagent, or a later turn that re-derives
  claims) re-runs the same checks and reads the diff against the spec. It
  must not treat the implementer's PR text as evidence.
- Same-model rubber-stamping is not a pass. If a second agent cannot be
  launched, the implementer still cannot mark review done; stop at "checks
  ran, independent review pending".

## Loop

```text
spec + checks + stop-loss
        |
        v
   implement (attempt n)
        |
        v
   run checks ---- pass ----> independent review ---- pass ----> record + Draft PR
        |                         |
        fail                      fail
        |                         |
        +-- n < max: retry implement (do not widen scope)
        |
        +-- n == max, or spec is the defect: stop, record, escalate
```

Widening scope, editing autonomy policy, or "fixing" CI to make a red check
green is a stop, not a retry.

## Stop-loss

Default: **3** implement attempts. Exhaustion is a successful use of the
loop: it proved the spec or the checks are wrong. Record that and ask the
Founder or rewrite the spec; do not burn a fourth attempt.

## Record

Fill `docs/templates/verify-retry-record.md` (or the same fields in the
Draft PR). Without a record, the loop did not happen.

## This change's own checks

The first use of this loop is the patch that adds it. Checks:

1. `docs/verify-retry-loop.md` and `docs/templates/verify-retry-record.md` exist.
2. `docs/agent-operating-loop.md` links here.
3. This file still forbids extra production mutation (`deploy` outside
   default-branch workflow). Merge follows `docs/fleet-merge-policy.md`.
4. Attribution to the source article remains.
5. `git diff --check`
6. `python3 scripts/validate-company-agent-contract.py`
7. `python3 -m unittest tests.test_governance_baseline tests.test_verify_retry_loop`
