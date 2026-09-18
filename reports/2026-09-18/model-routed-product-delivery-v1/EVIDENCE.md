# MODEL_ROUTED_PRODUCT_DELIVERY_V1 — evidence

**Date:** 2026-09-18  
**Sessions:** portfolio-ops `75136e841ed44612a7c8152b4e637f24` · alltrue `165a4cebf94845da9fc983493c05db3a`  
**Final status:** `PARTIAL` / `CAPACITY_BLOCKED` for live Sol→worker strong-planning acceptance

## 1. Before / after

| Gap | Before | After |
|---|---|---|
| Portable dual-axis + roles | Attachment-only / vague Skill mention | `docs/model-routed-product-delivery.md` + agent-operating-loop pointer |
| Plan handoff template | Missing | `docs/templates/strong-plan-handoff.md` |
| Cursor fail-closed resolve | Missing | `agent-control/bin/model-route-resolve` + `provider-model-map.toml` |
| Versioned `codex-route` | `~/.local/bin` only | Also `agent-control/bin/codex-route` (not auto-installed this run) |
| AllTrue entry | No dual-axis | Skill + `INAPP_PRODUCT_LOOP_EXECUTION_POLICY_V1` reference portable contract |
| Live Sol planning evidence | Unknown | Cursor Sol + Codex Luna/Sol **usage limit** — not accepted as strong Plan |

**Reused, not rebuilt:** `~/.codex/model-routing.toml`, profiles, `codex-route` fail-closed, agent-start, In-App Skill entry, H3/leases untouched.

## 2. Role → model evidence

| Role | Requested | Tool-reported / resolve | Evidence grade | Limit |
|---|---|---|---|---|
| Planning (Sol) | `gpt-5.6-sol-medium` (Cursor) / `gpt-5.6-sol` (Codex) | Cursor CLI: usage limit error; listed in `agent models` | Config + error | CAPACITY_BLOCKED until Cursor cycle / Codex credits |
| Astra | `gpt-6-astra` | Cursor map empty → fail-closed; Codex profile exists | Config + fixture | Cursor unavailable |
| Implementation (Luna) | `gpt-5.6-luna` | Codex exec: usage limit Sep 19 2026 4:26 PM | Config + error | CAPACITY_BLOCKED |
| Session light (Composer) | `composer-2.5-fast` | CLI returned `COMPOSER_OK` | Live tool | Available; **not** a Sol substitute |

Natural-language model self-claim: unused.

## 3. Plan / handoff

- Planning source for this wiring: Founder attachment `ALLTRUE_AGENT_OPERATING_MODEL_AND_NEXT_ACTION.md` §3 (not Sol-verified).
- Worker: this Cursor Composer session implemented bounded wiring only.
- Live **Sol→Luna** handoff: **not achieved** (capacity). Do not treat Composer wiring as strong-model acceptance.

## 4. Six acceptance cases

| Case | Result | Mode |
|---|---|---|
| Explicit small fix route | `codex-route` / resolve → luna for low batch | live dry-run + fixture |
| Complex authorized → strong Plan → light worker | **BLOCKED** (Sol/Luna quota) | live attempt failed; wiring docs ready |
| Strong model unavailable | resolve fail-closed; no composer substitute | fixture + live Sol error |
| Plan deviation → Lead | documented in handoff template | doc (not E2E agent chat) |
| Protected decision | plan OK, `implementation_allowed=false` | fixture |
| Fresh session resume | plan_ref checkpoint fixture | fixture |

Unit: `python3 -m unittest tests.test_model_routed_product_delivery -v` → 6 OK.

## 5. Persistence

See PR heads for portfolio-ops and AllTrue. Machine overrides (`~/.codex/config.toml`) unchanged. Runtime `agent-control` install **not** applied this run (avoid disturbing shared gateway).

## 6. Founder exceptions / deferred

- Raise Cursor Spend Limit / wait for cycle (stated reset 2026-10-12) and/or Codex credits (retry after 2026-09-19 16:26) for the **single** deferred live case: Sol Plan → Luna worker handoff with provider-reported model metadata.
- Runtime wake/H4B: untouched; still not claimed.
- Astra on Cursor: still unavailable in map.

## 7. One-line entry verification

| Surface | Verified |
|---|---|
| Cursor Skill path | Edited in AllTrue worktree; entry still `處理 in-app 意見與建議` |
| Codex | Same Skill/policy once quota restores; routing docs point at existing policy |
| CubeLV | Reference only; auto-dispatch not claimed |
