# Portfolio freshness re-baseline — 2026-08-27

## Result

The previous portfolio snapshot was stale: `updated_at` was 2026-08-09 and
both production projects had last-verified evidence from 2026-08-08. This
re-baseline records current GitHub, deployed-version, health, and workspace
evidence without changing product data or deleting any checkout.

| Project | Production identity | Health | Open P0 | Open P1 | Open issues | Open PRs |
|---|---|---|---:|---:|---:|---:|
| AllTrue | `5e6598052299386bbf13e12ae320b90186022348` | `ok`, 2026-08-27 10:04:10 +08:00 | 0 | 33 | 78 | 9 |
| Sunrise Cafe | `f8927b174b04ff7e026be5f4cb341396e1d120c6` | `ok=true`, 2026-08-27 10:04 +08:00 | 0 | 3 | 4 | 3 |

## Evidence

- AllTrue `/api/v1/health` returned HTTP 200 and `status=ok`.
- AllTrue `/version.json` reported build `5e659805`, built 2026-08-26 17:18:25
  UTC. The new director booking fix is not in this production identity yet.
- Sunrise `/api/booking-health` returned `ok=true`, with
  `rate_limit_grade=degraded_per_isolate` and `stripe_enabled=false` still
  explicitly visible.
- Sunrise `/api/version` reported deployed commit
  `f8927b174b04ff7e026be5f4cb341396e1d120c6`.
- AllTrue PR #2086 is open, mergeable, has all required CI checks green, and
  has no independent review yet. It is the current release candidate for the
  Xindian eighth-session workflow fix.

## Freshness policy outcome

The portfolio files now use 2026-08-27 evidence anchors and the exact deployed
commits. This evidence authorizes prioritization and review preparation only;
it does not authorize a production merge, deploy, attendance mutation, or
billing correction.
