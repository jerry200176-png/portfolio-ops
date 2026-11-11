# Portfolio documentation and reference refresh — 2026-10-24

## Decision and scope

Design record: [portfolio-ops #146](https://github.com/jerry200176-png/portfolio-ops/issues/146).
This is a documentation/metadata reconciliation in Portfolio Ops only. It creates
no scheduler, permission, API, installation, product change or private export.

The symptom was stale July–September snapshots plus wrong AllTrue stack claims.
The root cause was navigation and descriptive metadata not being reconciled when
the existing governance/product sources changed. Reuse the existing files,
read-only identity probe and freshness validator; reject a new registry or
date-only refresh. No product UI or competitor feature is being designed.

## Reproducible observations

- Portfolio base: `96de7c296f57bf57f7dfdd46f2deb03a5946b1c7`; fresh isolated research clone, clean before edits.
- Public GitHub observation: `2026-10-24T05:03:26Z`.
- Runtime observation: `2026-10-24T05:04:35.951151+00:00` via the unmodified
  `scripts/check-production-identity.py` (GETs and GitHub reads only).
- Complete public Star observation: `2026-10-24T05:08:32.839555+00:00`, one page at
  `per_page=100`; **64 distinct repositories**, all returned public metadata.
  `reference-repositories.yaml` records the complete set separately from the
  62 historical curation entries. A missing Star is not a deletion/adoption decision.
- Public snapshot: [JSON](portfolio-public-observation.json). It contains only
  public repository metadata and redacted probe outputs, not private implementation.

| Product | Repository head | Public serving SHA / health | Open labelled P0 / P1 |
|---|---|---|---|
| AllTrue | `219c4ab0bca2d79fece44646b2457bc80acbcba0` | `9401260000a10070bedf765148395942f96f7479` / HEALTHY | 1 / 40 |
| Sunrise | `73416404bfd55872b7354e477c959b68d4deb331` | `73416404bfd55872b7354e477c959b68d4deb331` / DEGRADED, memory / degraded_per_isolate | 0 / 4 |

Counts use open **issues**, excluding PRs, with the exact `priority:p0` and
`priority:p1` labels. Reproduce with GitHub issue search or paginated REST;
queries and observation times are in the JSON. The AllTrue labelled P0 is
[#1387](https://github.com/jerry200176-png/AllTrue_System/issues/1387).
Its label is not proof of a new active leak, containment or credential rotation.
No issue is closed, credential inspected/rotated or production state repaired.
Sunrise's degraded rate-limit observation remains a product finding, not a fix.

Repository main, serving SHA, merge/deploy state, health, artifact digest and
product acceptance are different facts. Do not infer one from another. Serving
SHA plus public health was observed; product acceptance and artifact digest
remain UNKNOWN. Pending activation/blocker state was not established.

## AllTrue source facts

Pinned application source: [`219c4ab`](https://github.com/jerry200176-png/AllTrue_System/commit/219c4ab0bca2d79fece44646b2457bc80acbcba0).
AllTrue #4482 changed only two docs; the application blobs are the same as its
reviewed base/head. Source was read statically; product tests were not rerun here.

- [backend/composer.json](https://github.com/jerry200176-png/AllTrue_System/blob/219c4ab0bca2d79fece44646b2457bc80acbcba0/backend/composer.json): Laravel `^8.75`,
  platform PHP `8.2.30`, plain `phpstan/phpstan ^2.0`; no declared Larastan,
  Filament/Livewire, Spatie Permission, LINE SDK or Telegram SDK dependency.
- [frontend/package.json](https://github.com/jerry200176-png/AllTrue_System/blob/219c4ab0bca2d79fece44646b2457bc80acbcba0/frontend/package.json): Vue `^3.5.43`,
  Vite `^6.4.4`; [supabase.js](https://github.com/jerry200176-png/AllTrue_System/blob/219c4ab0bca2d79fece44646b2457bc80acbcba0/frontend/src/supabase.js) is a local
  `/api/v1` adapter, not evidence of a hosted Supabase application backend.
- [database config](https://github.com/jerry200176-png/AllTrue_System/blob/219c4ab0bca2d79fece44646b2457bc80acbcba0/backend/config/database.php) defaults to MySQL.
- [LinePush.php](https://github.com/jerry200176-png/AllTrue_System/blob/219c4ab0bca2d79fece44646b2457bc80acbcba0/backend/app/Services/Line/LinePush.php) uses Laravel HTTP;
  [LineWebhookController.php](https://github.com/jerry200176-png/AllTrue_System/blob/219c4ab0bca2d79fece44646b2457bc80acbcba0/backend/app/Http/Controllers/LineWebhookController.php)
  and [signature tests](https://github.com/jerry200176-png/AllTrue_System/blob/219c4ab0bca2d79fece44646b2457bc80acbcba0/backend/tests/Feature/LineWebhookSignatureTest.php)
  establish LINE implementation alongside the Telegram handlers. SDK installation
  and channel implementation are deliberately distinguished.
- Existing routing/transfer limits come from the
  [AllTrue reference index](https://github.com/jerry200176-png/AllTrue_System/blob/219c4ab0bca2d79fece44646b2457bc80acbcba0/docs/architecture/STARRED_REPOSITORY_REFERENCE_INDEX.md), not new package adoption.

AllTrue/Sunrise source and documentation are proprietary; Portfolio had no
repository license at this base. GitHub SPDX metadata is a discovery observation,
not a component/license-body review. No external code or textbooks are copied.
Historical curation decisions remain dated; current-star license/availability
metadata is marked as metadata rather than fresh implementation/test evidence.

## Paths, precedence and unverified areas

RULEBOOK section 9 already retired Exo, local gateway/preflight and provenance;
the current default is a cloud session, fresh clone, branch and PR. Root entries
now point there instead of prescribing fixed workstation paths. `local_path`,
old no-edit boundaries and the old workspace manifest remain historical records;
no path is assumed present, promoted, moved, deleted or used as an edit target.

Private research internals, other local projects, workstation/process/WIP state,
Gmail signals, historical governance scores and old queue-item completion were
not revalidated. Their dates/UNKNOWN scope are retained; there is no new access
grant or private source finding in this public report. Retired local code and
machine contracts are retained unchanged, not re-enabled through documentation.
PR #138 owns checklist/hook portability; its files and permissions are untouched.

## Validation and rollback

Run existing rulebook, governance/company contract, company-context, freshness
and relevant test checks. The diff must contain only the named Markdown and
inventory/evidence YAML/JSON paths; no scripts, tests, workflows, settings,
rulebook/lock, machine contracts, catalog or workspace manifest changes.
Independent final-head review and GitHub checks are recorded in the PR.
Rollback is a normal documentation revert. This task ends at the requested
docs-only PR; no merge, schedule activation or permission change is included.

Local checks: rulebook pin, governance contract, company contract, company
context, blocking inventory freshness and whitespace checks passed. Existing
freshness tests passed 6/6; production-identity tests passed 12/12. Rulebook
tests passed 3/4 on Windows: the temporary-fixture stale-phrase parser test
writes CRLF and fails its LF-shaped assertion. The actual unchanged rulebook
pin/adapters check passes. No test, threshold or guard was changed; the normal
Linux GitHub job must independently check the full suite. The existing P0
evidence warning remains visible; a fresh label count is not issue resolution.
