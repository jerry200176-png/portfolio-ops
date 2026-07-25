# GitHub Starred Repositories — Benchmark Library

Read-only/curation task. No product repositories touched, no full portfolio
triage run. Full machine-readable data: `../../reference-repositories.yaml`.

## Starting point

40 existing stars (2 of which are the Founder's own product repos —
`jerry200176-png/sunrise-cafe`, `jerry200176-png/AllTrue_System` —
excluded from categorization below, since they're not reference material).

## Existing-star inventory by category

| Category | Existing count | Assessment |
|---|---|---|
| SaaS Product & UX | ~20 | **Heavily over-represented.** Multiple redundant generic design systems (carbon, fluentui, primer) and a cluster of generic finance/ERP/invoicing apps (firefly-iii, akaunting, frappe/erpnext, kimai, invoiceninja, crater) not tied to a specific current technical problem. |
| Next.js & Vercel | 5 | Reasonable core (supabase, line-bot-sdk-nodejs, radix-ui/primitives, shadcn-ui/ui, awesome-shadcn-ui) but **missing** anything on Stripe, Upstash/rate-limiting, or deployment governance — all live open problems for Sunrise right now. |
| Laravel & PHP | 6 | Decent (telegram SDKs, sentry-laravel, laravel-permission, filament) but **missing** PHPStan/larastan (AllTrue's own required CI check!) and any audit-trail package. |
| Reliability & Observability | ~1 | **Nearly empty** as a distinct category — only sentry-laravel, dual-counted from Laravel & PHP. |
| Security & Governance | ~2 | Thin — laravel-permission (dual-counted) and cloudflare/security-audit-skill. Nothing on secret-scanning tooling (despite AllTrue's CI already running gitleaks!) or CI/CD hardening. |
| AI Agent & Developer Experience | ~7 | Present but skewed toward "AI design taste" skills; **missing** anything on agent/hook governance, GitHub Actions automation for Claude Code, or agent SDK patterns — directly relevant to this very repo's own architecture. |

## Gaps, duplicates, and stale/unclear items found

- **Duplicates**: `carbon-design-system/carbon`, `microsoft/fluentui`,
  `primer/css` — three generic design systems, no tie to either product's
  actual stack.
- **Stale**: `crater-invoice-inc/crater` — last push 2024-08-10 (~2 years).
- **Moderately stale**: `argyleink/open-props` — last push ~6 months ago,
  and not tied to either product's styling approach anyway.
- **Unclear utility / low signal**: `pacifio/ui` (151 stars, single-purpose
  niche), `nextlevelbuilder/ui-ux-pro-max-skill` (naming/provenance is
  suspicious relative to its very high star count for an otherwise obscure
  account — flagged for the Founder to re-verify, not assumed legitimate
  just because the count is high).
- **Genre-inspiration cluster, not problem-tied**: firefly-iii, akaunting,
  frappe/erpnext, kimai, invoiceninja — five different finance/ERP/
  time-tracking apps with no specific current technical problem behind
  them. `GibbonEdu/core` is the one exception in this space worth keeping
  — it's the same domain as AllTrue (school operations).

None of the above were removed. Per your instruction, they're listed here
and in `reference-repositories.yaml` (`status: existing_cleanup_candidate`)
with reasoning, for you to decide.

## New candidates evaluated

Searched against each product's stated real needs (AllTrue: Laravel,
PHPStan, permissions, audit trail, scheduling, data correctness,
observability; Sunrise: Next.js, Vercel, Supabase, Stripe, LINE, deployment
governance; Portfolio OS: Claude Code, agents, hooks, workflow governance,
GitHub automation). Every candidate was checked for: relevance to a real
open item, last-push recency, license, and (via README/repo metadata)
apparent test/CI presence, before being scored.

**13 accepted and starred** (full detail, including the ones evaluated and
rejected, in `reference-repositories.yaml`):

| Category | Added | Why |
|---|---|---|
| Next.js & Vercel | `supabase/supabase-js`, `upstash/ratelimit-js`, `vercel/examples` | Official Supabase client; closes SEC-SUNRISE-002's undecided rate-limiting item directly; official Vercel pattern reference |
| Laravel & PHP | `larastan/larastan`, `spatie/laravel-activitylog` | Larastan powers AllTrue's own "PHPStan Advisory" required check; activitylog is the audit-trail gap |
| Reliability & Observability | `spatie/laravel-schedule-monitor`, `spatie/laravel-health`, `open-telemetry/opentelemetry-php` | Scheduling reliability, structured health checks, standard PHP observability — category was nearly empty |
| Security & Governance | `gitleaks/gitleaks`, `step-security/harden-runner`, `ossf/scorecard` | gitleaks documents a tool AllTrue's CI *already runs*; harden-runner and scorecard are direct fits for portfolio-ops's own governance mission |
| AI Agent & DevEx | `anthropics/claude-code-action`, `anthropics/claude-agent-sdk-python` | Official Claude Code GitHub Action (workflow governance/automation) and the official agent SDK, informing this repo's own `.claude/agents/` design |
| SaaS Product & UX | *(none)* | Already saturated (~20 existing) — see cleanup notes above instead |

## Rejected candidates

| Repo | Reason |
|---|---|
| `vercel/nextjs-subscription-payments` | Archived — topical match (Stripe+Next.js) but stale |
| `owen-it/laravel-auditing` | Redundant with accepted `spatie/laravel-activitylog` |
| `grafana/k6`, `grafana/grafana` | No active load-testing/metrics-stack initiative on either product; heavy for current scale |
| `open-policy-agent/opa` | Current governance is lightweight Python hooks (`guard_bash.py`) — OPA is a real capability upgrade but not justified by current complexity |
| `sigstore/cosign` | No artifact-signing/supply-chain pipeline exists to apply it to |
| `anthropics/anthropic-sdk-typescript` | Redundant with accepted `claude-agent-sdk-python`; no direct-API use case currently |
| `vercel/turborepo` | Neither product is a monorepo |

## Remaining reference-library gaps

- **AllTrue data-correctness/idempotency patterns**: no strong candidate
  found this round for the specific "billing calc bug 0/2998 vs 3000"
  class of problem (issue #1096) — worth a dedicated search next time.
- **Sunrise mobile UX**: nothing added or found specifically addressing
  mobile-specific booking/reservation UX patterns — requested but no
  strong candidate surfaced.
- **Vercel deployment-governance specifically** (multi-project hygiene,
  preview-deploy management at the account level): no repo-level reference
  really covers this — it's more of an account-configuration practice than
  something a starred repo teaches. Noted as a gap that reference material
  can't fully close; ties back to the Vercel duplicate-project finding from
  this session's earlier Sunrise forensics work.

## GitHub Lists — NOT created

Attempted via GraphQL (`createUserList`, `updateUserListsForItem` — both
exist and are reachable; read access to your 5 existing lists — "自有系統",
"AI記憶", "Agent流程", "UI/UX", "ERP/財務" — worked fine). **Write access
failed**: `INSUFFICIENT_SCOPES` — the authenticated token has
`gist, project, read:org, repo, workflow` scopes but list mutations require
the `user` scope, which isn't granted. This is a real, current blocker, not
something worked around or faked. If you want Lists created, the token
needs the `user` scope added at
`https://github.com/settings/tokens` — no Founder action beyond that is
needed, since the mutations themselves are confirmed to work.

## How Portfolio OS should query this library going forward

- **Source of truth**: `reference-repositories.yaml` at the repo root —
  structured, one entry per repo, with `category`/`relevant_to`/`use_for`/
  `status` fields designed to be grepped or parsed by the
  `reference-repo-researcher` agent and the `checklists/reference-repos.md`
  procedure, instead of that agent doing a fresh GitHub search every time.
- Filter by `relevant_to: [alltrue]` / `[sunrise]` / `[portfolio-ops]` to
  scope to one product; filter by `status: added` or `existing_kept` to
  exclude cleanup candidates and rejected entries from active
  recommendations.
- Re-run this curation periodically (e.g., during `weekly-review` mode) to
  catch newly-relevant repos and re-check `existing_cleanup_candidate`
  entries for whether the Founder wants them pruned.
