# portfolio-ops agent guide

Portfolio control plane for jerry200176-png's products (AllTrue System, Sunrise Cafe). It
governs how agents triage, audit and maintain those products; it holds no product code.
Rules for every agent are in `governance/RULEBOOK.md` (canonical copy lives here). This file
only adds what is specific to this repository.

## Read order

1. `governance/RULEBOOK.md`, then this file.
2. `.claude/skills/portfolio-maintain/SKILL.md` and the mode file you are running.
3. `portfolio.yaml`, `CEO_DASHBOARD.md` and `state/work-queue.yaml` for current state.
4. For product work: the product repo's own `AGENTS.md`.

Operating loop and contract: `docs/agent-operating-loop.md`,
`governance/company-agent-contract.yaml`. Rationale: `docs/security-boundaries.md`,
`docs/evidence-policy.md`, `docs/prioritization.md`. History: `governance/DECISIONS.md`.

## Commands (what CI runs)

```bash
python -m unittest discover -s tests -v
python scripts/check-rulebook.py
python scripts/validate-governance-contract.py
python scripts/validate-company-agent-contract.py
python scripts/company-context.py --check
git diff --check
```

After editing `.claude/hooks/`, also run `python3 .claude/hooks/test_guard_bash.py`.

## Repo-specific rules

- A repo-maintaining agent works on exactly one repository per invocation.
- Editing `governance/RULEBOOK.md`: update `governance/rules.yaml` IDs and the `sha256` in
  `governance/RULEBOOK.lock` in the same PR, and add a `governance/DECISIONS.md` entry when a
  rule changes. Product repos then re-vendor with `scripts/check-rulebook.py --update <sha>`.
- `agent-control/` and `docs/workspace-entrypoints/` are the retired local gateway; do not
  require them.
