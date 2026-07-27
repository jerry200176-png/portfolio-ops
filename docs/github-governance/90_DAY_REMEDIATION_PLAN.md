# 90-Day Remediation Plan — 2026-07

Proportionate to criticality. Prefer reversible changes. Items marked **DECISION** require Founder approval.

## Days 0–30 (quick wins / visibility)
1. Merge/land this audit docs PR on portfolio-ops; create umbrella Issue.
2. Grant Operator App **read-only** security alert permissions (PERMISSION_GAPS) — **DECISION**.
3. Enable `delete_branch_on_merge` on portfolio-ops + korea-trip-plan — **DECISION**; delete high-confidence merged branches listed.
4. Add `timeout-minutes` + PR `concurrency` to workflows missing them (Phase 9 style PRs, per-repo).
5. Sunrise: confirm autonomous-loop remains disabled; document minutes recovered; open dedicated Issue for Vercel prod capacity if still missing.
6. AllTrue: inventory one-off `ops-*` / diagnose workflows; propose archive/disable list — **DECISION** before deleting workflows.

## Days 31–60 (reliability & supply chain)
1. Tier 0 Action pinning policy: SHA pin deploy + required checks (or enable `sha_pinning_required`) — **DECISION**.
2. AllTrue Presubmit fail-rate reduction: split flaky checks vs true blockers; align required check names (no silent drift).
3. Sunrise Verify Production flake budget + SLO; keep deploy sole owner.
4. student-evaluation: remove committed `node_modules` or archive repo — **DECISION**.
5. income-statement-app-releases: confirm mirror/archive; freeze write access if archive — **DECISION**.

## Days 61–90 (operating model)
1. AllTrue Issue/PR WIP limit + bot PR evidence template enforcement.
2. portfolio.yaml expand to include all 9 installation repos (today only AllTrue+Sunrise fully tiered).
3. Quarterly branch hygiene automation (dry-run already exists on AllTrue) extended to korea-trip + portfolio-ops.
4. Re-audit security alerts after permission grant; close or escalate P0 vulns.
5. Measure Actions minutes before/after; stop if ROI negative.

## Explicit non-goals (90d)
- No enterprise cargo-cult rulesets on Tier 3/4.
- No autonomous production deploy changes.
- No mass issue closure.
- No force push / history rewrite.
