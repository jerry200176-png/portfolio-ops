# Research decision record — fleet merge after required checks

- Problem and success criteria:
  Remove the blanket never-merge rule. Portfolio-ops remains fleet authority.
  Agents squash-merge R0–R2 when required GitHub checks are green. Founder
  keeps R3, extra deploy, data repair, credentials, Gmail, issue close.
- Official or primary source:
  Founder direction 2026-08-15 (human rubber-stamp of unread CI is not a
  control). AllTrue `RISK_BASED_MERGE_POLICY.md` already allowed R0 agent
  merge; fleet table had forbidden it.
- Mature-company practice:
  Required status checks on the default branch as the merge gate; no
  second human who will not re-derive the suite.
- Maintained open-source/starred repository:
  GitHub rulesets already require validate/CodeQL/secret scan on
  portfolio-ops; AllTrue Presubmit + provenance.
- Transferable pattern:
  Checks = acceptance; merge ≠ extra production mutation.
- What does not transfer:
  Auto-merge R3; `--admin`; Gmail; issue close; credential rotation.
- License and fit review:
  Internal policy only.
- Adoption cost and smallest experiment:
  This docs/policy PR. After merge, agents follow the new table.
- Decision and GitHub issue/PR:
  Adopt; PR filled when opened. Risk-Class: R0.
