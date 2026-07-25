# Reference repository research checklist

Delegate to `reference-repo-researcher` (read-only, no cloning of arbitrary
starred repos). Never bulk-clone starred repositories.

For each Tier 0/1 project with a live, specific problem, pick at most 3–5
reference repos that are:

- directly relevant to the current stack, product type, or UX problem
- still maintained recently
- well-documented and well-tested
- architecturally mature, with a clear license
- chosen for demonstrable patterns, not star count

## Analyze, per reference repo

Product pattern, UX pattern, architecture boundaries, error handling,
observability, CI/testing, release/rollback approach, any agent-governance
pattern, what doesn't transfer here, adoption cost, expected value.

Produce **improvement hypotheses only** — do not copy code wholesale and do
not propose a large unevidenced rewrite. A hypothesis becomes a real task
only after it clears the prioritization formula in
`../../../../docs/prioritization.md`.

## Output

`reports/YYYY-MM-DD/reference-repos.md`.
