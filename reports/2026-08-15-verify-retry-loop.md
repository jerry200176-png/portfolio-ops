# Verify-retry record — add inner loop (pilot)

- Task / GitHub issue: portfolio-ops `verify-retry-loop-20260815`
- Eligible class: T0 docs (portfolio-ops `docs/`, templates, one unit test)
- Spec (paths in / paths out / outcome):
  - In: `docs/verify-retry-loop.md`, `docs/templates/verify-retry-record.md`,
    `docs/research/2026-08-verify-retry-loop.md`, operating-loop pointers,
    execute/execution-standards, workspace entrypoints, contract inner_loop
    pointer, `tests/test_verify_retry_loop.py`
  - Out: `governance/AUTONOMY_POLICY.md`, merge/deploy authority, AllTrue/Sunrise
    product code, `.github/workflows`
  - Outcome: eligible T0/T1 work has a written inner loop; Founder gates unchanged
- Checks (exact commands):
  - `git diff --check`
  - `python3 scripts/validate-company-agent-contract.py`
  - `python3 -m unittest tests.test_governance_baseline tests.test_verify_retry_loop`
- Stop-loss (max attempts, default 3): 3
- Attempt log:

| n | What changed | Check command | Result | Retry target (implement / spec) |
|---|---|---|---|---|
| 1 | Add SOP, record template, research note, pointers, unit test | unittest + contract + diff --check | pass | — |

- Independent review: code-reviewer subagent re-ran the same checks; No findings; spec met
- Exhausted?: no
- Draft PR: not opened (waiting Founder if commit/PR is wanted)
- Founder-gated leftover (merge/deploy/other): still required
