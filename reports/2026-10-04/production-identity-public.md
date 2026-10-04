# Production identity — public snapshot

**Generated:** `2026-10-04T08:14:55.422760Z` by
`scripts/check-production-identity.py` with `github_fetch=None` (public HTTP
endpoints only). AllTrue's public deployment manifest was checked at 08:11Z;
Sunrise's booking-health detail was checked at 08:11Z.

| Product | Runtime state | Serving SHA | Health | Inventory SHA | Match |
| --- | --- | --- | --- | --- | --- |
| AllTrue | `RUNTIME_VERIFIED` | `e483c1dc43975cfa173b12e75376fa51dc107a30` | `status=ok` | `e17d36ba838d36e6598af9f9b1d27a1f2134c204` | No |
| Sunrise | `RUNTIME_VERIFIED` | `fec9e458767bd5b4a0e51cb440d4145440591ecc` | `ok=true`; rate limit degraded | `6630b9eb003e2d5459c84c9452f2413cc93ba8ab` | No |

`RUNTIME_VERIFIED` means the public version endpoint returned a full source
SHA and the configured health endpoint indicated service health during this
observation. Sunrise's booking health also returned
`rate_limit_grade=degraded_per_isolate` (`rate_limit_mode=memory`); `ok=true`
does not erase that degraded signal. This probe does not verify a changed
product journey or mark the work accepted.

AllTrue's `deployment.json` at the same observation reported backend,
frontend, and frontend build SHA `e483c1dc43975cfa173b12e75376fa51dc107a30`,
source `github-actions:deploy.yml`, and deployment time
`2026-10-03T22:11:33Z`. Neither public product endpoint exposes an artifact
digest, so artifact digest is `UNKNOWN` for both products.

| Product | Pending candidate | Protected blocker | Product acceptance |
| --- | --- | --- | --- |
| AllTrue | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` |
| Sunrise | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` |

The public workflow uses a repository-scoped token and cannot establish
private product deployment candidates or reviewer details. Runtime endpoints
alone cannot establish product acceptance. Those fields therefore remain
`UNKNOWN` in this public record.

## Freshness

The latest automated report is
[weekly governance run 37174146031](https://github.com/jerry200176-png/portfolio-ops/actions/runs/37174146031),
whose production identity artifact was generated at `2026-10-04T03:28:01Z`.
The workflow failed in two steps. The freshness report failed because
`portfolio.yaml` and status evidence were last verified on 2026-09-04. The
identity probe received healthy public endpoint responses, but its gate exited
with failure because both runtime SHAs differ from their recorded inventory
SHAs. Issue counts, priorities, and wider repository inventory remain stale
until a complete triage refresh; this runtime-only snapshot does not refresh
them.

Machine-readable public-only snapshot: `production-identity-public.json`.
