# Model-routed product delivery (portable contract)

**Status:** Active company contract (docs)  
**Goal id:** `MODEL_ROUTED_PRODUCT_DELIVERY_V1`  
**Not:** a new router platform, Goal authority, scheduler, or Founder-gate replacement.

Machine-authoritative Codex selection remains
`~/.codex/model-routing.toml` + installed `codex-route`.
This document holds **portable roles**, dual-axis routing semantics, evidence
rules, and Plan handoff expectations. Provider-specific model IDs for Cursor
live in `agent-control/config/provider-model-map.toml` (versioned, non-secret).

## Dual axis (difficulty ≠ authorization)

| Axis | Question | Effect |
|---|---|---|
| Difficulty / uncertainty | Is root cause unclear, cross-module, or a real engineering trade-off? | Route planning to **Sol** (Astra only when explicitly eligible and available). |
| Authorization | Does existing policy already allow implementation, or is this Founder-protected? | Strong plans **never** create new authority. Protected work still stops for Founder. |

Light models may propose a preliminary class; they must not self-label work as
“small fix” to exceed existing policy. When unclear → Sol judgment (when
available) or leave the item blocked without silent downgrade.

### Relation to AllTrue `PLAN_REQUIRED`

- **Auto-fix envelope** (product policy): approved light implementation profile.
- **Complex but already authorized** (behavior known or Founder GO already
  visible): Sol/Astra produce a bounded Plan → light worker implements that
  Plan revision. This is **not** a new permission.
- **`PLAN_REQUIRED`**: Founder Decision Packet. Sol may help gather evidence;
  it does **not** cancel the Founder gate. Do not rename `PLAN_REQUIRED` to
  bypass it.

## Portable roles

| Role | Tier | Responsibility |
|---|---|---|
| Planning Lead | `sol` (Astra if `sol_insufficient` + `astra_eligible` + model available) | Detailed engineering Plan with nine facets (N/A + reason OK). |
| Implementation worker | existing approved light profile (`luna` / Codex `implementation`) | Bounded code/test/docs against an explicit Plan revision. Do **not** promote a read-only profile to writer because of its name. |
| Reviewer | risk-appropriate independent review role | Reviews actual diff/head; does not become an approver of protected decisions. |
| Product Lead | session/operator role | Owns outcome, worker assignment, deviation handling, acceptance. Not the chat transcript. |

`auto` and fuzzy aliases are **forbidden** as the strong-model commitment.
If `inherit` is used, record the parent model and inheritance evidence.

## Provider ID owners

| Concern | Owner | Notes |
|---|---|---|
| Portable roles / dual axis / handoff | This doc + `docs/templates/strong-plan-handoff.md` | Committed in portfolio-ops. |
| Codex profile → model ID | `~/.codex/*.config.toml` + `model-routing.toml` | Machine-local; fail-closed for protected Sol. |
| Cursor role → model slug | `agent-control/config/provider-model-map.toml` | Non-secret; resolve with `agent models` / `--list-models`, never guess. |
| AllTrue one-line entry | AllTrue In-App Skill / execution policy | **References** this contract; does not fork routing rules. |

## Evidence grades

1. **Config evidence** — what was requested (tier, profile, map entry, CLI flags).
2. **Tool/provider session evidence** — task/run/plan ref, resolved configuration,
   provider-reported actual model (if any), reasoning effort, CLI/config version,
   fallback/quota/error.
3. **Natural-language self-claim** — not evidence.

If actual model cannot be observed, record `UNKNOWN`. If a non-allowed fallback
cannot be excluded, the Plan must **not** pass “strong planning accepted” and
must not auto-dispatch complex implementation. Keep other authorized small
fixes running.

## Fail-closed / capacity

- Protected Sol unavailable → fail-closed; item `CAPACITY_BLOCKED`; no silent
  downgrade to Terra/Luna/Composer for that planning commitment.
- Astra unavailable on Cursor (current account map) → do not pretend Astra ran;
  use Codex only when eligible and available, else leave Astra path blocked.
- Complexity-only Sol fallback to Terra+high is allowed **only** where the
  machine Codex policy already defines it; protected/workload Sol routes do not
  inherit that fallback.

## Plan handoff

Use [`docs/templates/strong-plan-handoff.md`](templates/strong-plan-handoff.md).
Workers read the refined Plan + cited evidence, not full chat or hidden
reasoning. Ordinary engineering deviation → Planning Lead. New product or
protected decisions → Founder. Bound retries; stop loops without progress.

## Resolver

`agent-control/bin/model-route-resolve` resolves a role/tier for `codex` or
`cursor` and prints JSON. It does not launch agents, mutate permissions, or
replace H3/leases/fencing.
