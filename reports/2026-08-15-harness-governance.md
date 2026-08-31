# Verify-retry record — harness-informed fleet governance

- Task / GitHub issue: portfolio-ops `harness-governance-20260815`
- Eligible class: T0 docs
- Spec (paths in / paths out / outcome):
  - In: closeout, journal template, HARD_LESSONS, small-project harness,
    operating-loop stall/closeout/intake pointers, contract fields, tests
  - Out: AUTONOMY_POLICY, AllTrue/Sunrise product trees, seven-file overlay
    on production products, merge/deploy authority
  - Outcome: stall, closeout, lesson promotion, and small-repo intake exist
- Checks (exact commands):
  - `git diff --check`
  - `python3 scripts/validate-company-agent-contract.py`
  - `python3 -m unittest tests.test_governance_baseline tests.test_verify_retry_loop tests.test_harness_governance`
- Stop-loss (max attempts, default 3): 3
- Attempt log:

| n | What changed | Check command | Result | Retry target (implement / spec) |
|---|---|---|---|---|
| 1 | Add harness-informed SOPs and tests | unittest + contract + diff --check | pass | — |

- Independent review: code-reviewer; No findings; spec met
- Exhausted?: no
- Draft PR: opening
- Founder-gated leftover (merge/deploy/other): still required
