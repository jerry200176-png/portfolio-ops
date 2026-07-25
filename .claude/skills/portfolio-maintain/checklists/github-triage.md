# GitHub triage checklist

Delegate to `github-triage` (read-only). For each Tier 0/1 project, read:

- open Issues, open PRs, recently closed Issues, recently merged PRs
- CI failures, deployment failures, security alerts (Dependabot/secret
  scanning)

## Find and flag

- duplicates, stale items, "fixed but not closed", "can't reproduce",
  evidence-free claims, items superseded by another PR, CI-blocked items,
  production incidents, UX regressions, high-value ownerless work

## Score

```
Priority = Impact × Confidence × Urgency ÷ Effort
```

See `../../../../docs/prioritization.md` for the full rubric. Keep at most 5
real next-steps per project — this is not a backlog dump. Never trust a
label (`P0`, `bug`, etc.) as ground truth by itself; cross-check against
code, tests, CI, and production evidence per `docs/evidence-policy.md`.

## Output

`reports/YYYY-MM-DD/github-triage.md`: per project, the shortlist with
evidence and score rationale. Update `state/work-queue.yaml` and
`portfolio.yaml`'s `open_p0`/`open_p1`/`current_priority`/`next_action`
fields from this pass — don't leave the dashboard citing stale numbers.
