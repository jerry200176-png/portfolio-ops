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
| GitHub baseline governance rulesets | Partial | `portfolio-governance-main` remains active on all 7 repositories with PR/CI, deletion, and force-push controls; the single-owner policy now intentionally requires no human approval. Four repositories still miss one or more declared adapters. | Weekly |
| ExoProtocol 0.2.3 pilot | Retired (2026-10-14) | Founder 2026-10-14（三）#6 retired Exo fleet-wide; tracked `.exo/` trees and the manual workflow are removed. | None |
| AllTrue production mutation | Unverified | Use repository capability registry and canonical workflow only | Before use |
| Sunrise production mutation | Partial | Vercel integration exists; recent failed deployments require fresh verification | Before use |

Never infer a missing capability from broad account ownership. Use the proven path or create a bounded capability test.
