# Capability registry

**Last verified:** 2026-07-19

| Capability | Status | Evidence | Review cadence |
|---|---|---|---|
| GitHub connector read | Proven | Authenticated profile and both repo/issue/PR reads succeeded | Weekly |
| GitHub connector write | Missing | Issue comment returned HTTP 403: integration cannot write | Weekly |
| GitHub CLI read/write | Proven | `gh auth status` and comment on AllTrue #1007 succeeded | Weekly |
| Gmail read/search | Proven | Profile, labels, searches, and message reads succeeded for `jerry200176@gmail.com` | Weekly |
| Gmail write/organize | Unverified | Must be proven with the first bounded label/archive action | Weekly |
| Local git | Proven | Both canonical repositories are clean and track `origin/main` | Daily |
| Codex scheduled automation | Partial | Existing cron discovered; company automations not yet verified | Weekly |
| AllTrue production mutation | Unverified | Use repository capability registry and canonical workflow only | Before use |
| Sunrise production mutation | Partial | Vercel integration exists; recent failed deployments require fresh verification | Before use |

Never infer a missing capability from broad account ownership. Use the proven path or create a bounded capability test.
