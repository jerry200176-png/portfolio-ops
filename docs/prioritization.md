# Prioritization

## Cross-portfolio priority order

1. Security, privacy, payment, permissions, and data correctness.
2. Production outage, data loss, or major operational blockage.
3. Real users hitting broken core flows.
4. CI, deployment, rollback, backup, and observability gaps.
5. High-frequency UX friction and state inconsistency.
6. Systemic tech debt that keeps generating bugs or slowing delivery.
7. Test, documentation, and governance gaps.
8. General refactors.
9. Pure cosmetic/naming/low-impact cleanup.

Do not reorder by ease. An easy Tier-9 task does not jump ahead of a harder
Tier-2 task.

## Per-item priority formula

```
Priority = Impact × Confidence × Urgency ÷ Effort
```

- **Impact**: how much this moves reliability, user-facing correctness, or
  business value if fixed — not how big the diff is.
- **Confidence**: how well the evidence supports the claimed problem and fix
  (see `docs/evidence-policy.md`). An unverified P0 report has low
  confidence until cross-checked.
- **Urgency**: how much worse this gets, or how much risk compounds, the
  longer it's left.
- **Effort**: realistic implementation + verification cost, including test
  and rollback work — not just the code change.

Score qualitatively (low/med/high) unless a numeric score is actually useful
for a specific comparison; the formula is a reasoning aid, not a scoreboard
to game.

Cap each project's live shortlist at 5 items. This is not a backlog dump —
if it doesn't make the top 5, it doesn't get tracked as "current work" (it
can still exist in GitHub Issues).

## Tiering (portfolio.yaml `tier` field)

- **Tier 0** — production-critical: active incident, billing/data/permission
  risk, real users blocked, deployment/reliability failure.
- **Tier 1** — core product: real users, recently active, clear business
  value.
- **Tier 2** — active but non-core: not yet production, or production with
  low risk, but has potential value.
- **Tier 3** — experimental, reference, paused, or archive candidate.

Re-tier when facts change (e.g. an incident resolves, a dormant repo gets
real usage) — tiering is a snapshot, not a permanent label.

## First-round scope (baseline audits and execution)

Prioritize: production reliability, real bugs, data/state inconsistency,
CI/deploy blockers, core UX friction.

Defer in the first round: full-repo reformatting, pure renames, large
rewrites, blanket dependency upgrades, large-scale file moves, and
documentation-only polish. These may be legitimate later, but not before the
Tier 0/1 reliability and correctness backlog is addressed.
