## Production identity (read-only observation)
Generated: `2026-10-04T10:55:10.118445+00:00`
RUNTIME_VERIFIED = full runtime SHA plus healthy endpoint; RUNTIME_DEGRADED / RUNTIME_UNHEALTHY = full SHA with corresponding health state; DEPLOYED = SHA observed but health unknown; UNKNOWN = no full runtime SHA. Product acceptance remains UNKNOWN; MERGED is not inferred from runtime endpoints.

| Product | Runtime state / SHA | Health details | Artifact digest | Inventory age / match | Pending candidate / age | Protected blocker | Product acceptance |
|---|---|---|---|---|---|---|---|
| alltrue | RUNTIME_VERIFIED / `e483c1dc43975cfa173b12e75376fa51dc107a30` (observed 2026-10-04T10:55:10.118445+00:00) | HEALTHY {} | UNKNOWN | 720h / NO (`e17d36ba838d36e6598af9f9b1d27a1f2134c204`) | `21cd3e0f2b75114ba66f9f59b6cde9edd87b3f2c` / 1h (WAITING) | ENVIRONMENT_REVIEW_REQUIRED | UNKNOWN |
| sunrise | RUNTIME_DEGRADED / `fec9e458767bd5b4a0e51cb440d4145440591ecc` (observed 2026-10-04T10:55:10.118445+00:00) | DEGRADED {"rate_limit_grade": "degraded_per_isolate", "rate_limit_mode": "memory"} | UNKNOWN | 720h / NO (`6630b9eb003e2d5459c84c9452f2413cc93ba8ab`) | `UNKNOWN` / UNKNOWNh (UNKNOWN) | UNKNOWN | UNKNOWN |

Evidence:
- alltrue candidate: https://api.github.com/repos/jerry200176-png/AllTrue_System/deployments/6839479493
- alltrue blocker: https://github.com/jerry200176-png/AllTrue_System/actions/runs/37193508312
## Exact runtime and release evidence

- Snapshot generated at: `2026-10-04T10:55:10Z`. Portfolio Ops main was
  `55a9eca71906162bc98730936aba50af14e16fb3` during generation.
- AllTrue GitHub main is `21cd3e0f2b75114ba66f9f59b6cde9edd87b3f2c`.
  Public `/deployment.json` reports backend, frontend, and frontend build all
  at `e483c1dc43975cfa173b12e75376fa51dc107a30`, deployed
  `2026-10-03T22:11:33Z` by `github-actions:deploy.yml`; `/api/v1/health`
  returned `status=ok`.
- GitHub compare reports the pending AllTrue candidate is 14 commits ahead of
  the serving SHA and 0 behind, spanning 61 paths including billing,
  accounting, schedule, UI, security, and CI changes. The candidate is not
  represented as a low-risk release. Deployment `6839479493` targets
  `production-activation`; run `37193508312` is waiting on the required
  Founder reviewer. No artifact digest or product acceptance evidence is
  available. The user's approval of portfolio-ops PR #119 does not approve
  this AllTrue production activation.
- Sunrise GitHub main and public `/api/version` both report
  `fec9e458767bd5b4a0e51cb440d4145440591ecc`. The public booking health
  endpoint returns `ok=true` but also `rate_limit_mode=memory` and
  `rate_limit_grade=degraded_per_isolate`, so this is DEGRADED.
- Sunrise reminder workflow `37139788688` step failed at
  `2026-10-03T17:16:03Z`; the workflow ended at `2026-10-03T17:16:06Z` during “Resolve CRON_SECRET + run send-line twice +
  verify”. It failed before the second request and verification. Cause and
  possible first-request side effect are UNKNOWN. The workflow was not
  rerun. Vercel's request log needs credentialed read-only access to resolve
  the generic `MIDDLEWARE_INVOCATION_FAILED` safely.
- Portfolio issue counts and priorities still come from inventory last
  refreshed `2026-09-04`; they remain stale pending a separate full triage.
  Runtime version evidence does not refresh issue counts or imply product
  acceptance.

## Delivery-control fixes independently verified

- AllTrue PR [#3517](https://github.com/jerry200176-png/AllTrue_System/pull/3517)
  merged as `5ba434c8bd3b7451d9f7e7228766a64556f4c10f`, granting the
  convergence workflow only the missing `pull-requests: read` scope. The
  seven 403 failures were runs
  [37186363748](https://github.com/jerry200176-png/AllTrue_System/actions/runs/37186363748),
  [37186568844](https://github.com/jerry200176-png/AllTrue_System/actions/runs/37186568844),
  [37186654238](https://github.com/jerry200176-png/AllTrue_System/actions/runs/37186654238),
  [37186667144](https://github.com/jerry200176-png/AllTrue_System/actions/runs/37186667144),
  [37186921293](https://github.com/jerry200176-png/AllTrue_System/actions/runs/37186921293),
  [37186971682](https://github.com/jerry200176-png/AllTrue_System/actions/runs/37186971682),
  and [37188607616](https://github.com/jerry200176-png/AllTrue_System/actions/runs/37188607616).
  The first API read was blocked because `pull-requests: read` was absent.
  Later run `37194841048` passed the repaired PR read. Runs `37195638846`
  and `37196297336` also passed that read but ended their bounded wait because
  source PR #3520 was still open; neither dispatched exact-main CI or a
  production handoff. The 10:43 run status was success for this no-op/fallback
  path, not proof that #3520 merged.
- A separate main push CI failure `37186403977` was caused by missing git
  credentials for `dorny/paths-filter` fetch, not PR-read permission. AllTrue
  PR [#3519](https://github.com/jerry200176-png/AllTrue_System/pull/3519)
  fixed that on main SHA
  `21cd3e0f2b75114ba66f9f59b6cde9edd87b3f2c`.
- AllTrue PR [#3516](https://github.com/jerry200176-png/AllTrue_System/pull/3516)
  merged as `013cf69dbfe2e5a0b50a0a6a147e448ebf332919`. UI Smoke uses
  `ui-smoke-${{ github.event.pull_request.number || github.run_id }}` and
  cancels in progress only for `pull_request` events. The PR's exact-head
  required checks, including UI Smoke, passed.

