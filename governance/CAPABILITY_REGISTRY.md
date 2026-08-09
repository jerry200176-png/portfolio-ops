# Capability registry

**Last verified:** 2026-08-09

| Capability | Status | Evidence | Review cadence |
|---|---|---|---|
| GitHub connector read | Proven | Authenticated profile and both repo/issue/PR reads succeeded | Weekly |
| GitHub connector write | Missing | Issue comment returned HTTP 403: integration cannot write | Weekly |
| GitHub CLI read/write | Proven | `gh auth status` and comment on AllTrue #1007 succeeded | Weekly |
| Gmail read/search | Proven | Profile, labels, searches, and message reads succeeded for `jerry200176@gmail.com` | Weekly |
| Gmail write/organize | Proven | Created and applied `AI Company/Security/P0` to four selected GitGuardian messages | Weekly |
| Local git | Proven | Canonical checkouts and isolated governance worktrees were inspected; existing user changes were preserved | Daily |
| Codex scheduled automation | Proven | Daily loop, weekly governance review, and P0/P1 watch created and rendered in the app | Weekly |
| GitHub baseline governance rulesets | Partial | Read-only audit confirms `portfolio-governance-main` is active on all 7 repositories, but AllTrue currently has no required human review; four repositories still miss one or more declared adapters. Existing ruleset drift is report-only until an explicit replacement decision. | Weekly |
| ExoProtocol 0.2.3 pilot | Partial | Isolated `engineering-intelligence` pilot evidence exists; the Exo workflow is not present across the seven-repository fleet and generated adapters/CI remain Draft-PR work. | Per repo rollout |
| AllTrue production mutation | Unverified | Use repository capability registry and canonical workflow only | Before use |
| Sunrise production mutation | Partial | Vercel integration exists; recent failed deployments require fresh verification | Before use |

Never infer a missing capability from broad account ownership. Use the proven path or create a bounded capability test.
