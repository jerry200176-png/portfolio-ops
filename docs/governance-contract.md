# Company governance contract

This repository is the source for company-level governance metadata. Product
repositories keep their own overlays, but all overlays must expose the same
component contract and be checked by the same validation workflow.

## Required component fields

Each component record under `catalog/` must identify its owner, lifecycle,
tier, data sensitivity, deploy target, health URL, version URL, recovery owner,
last verification time, and evidence TTL.

The contract is intentionally Backstage-compatible without requiring Backstage.
The YAML files can later be registered in a catalog, while the current control
plane validates them locally and uses them to generate portfolio reports.

## Enforcement boundary

The declarative GitHub policy lives at
`governance/github-enforcement-policy.yaml`. Applying or changing GitHub
rulesets remains a Founder-approved external action. The audit may report
drift, but it must not change rulesets, merge pull requests, deploy, or alter
production data.

## Freshness

`portfolio.yaml` records `last_verified_at`, `source_commit`, and
`evidence_expires_at` for each production project. Expired evidence is stale:
it may inform triage but cannot authorize incident closure, merge, deploy, or
production mutation.
