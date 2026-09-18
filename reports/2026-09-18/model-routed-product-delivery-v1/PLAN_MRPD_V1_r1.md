# Plan MRPD-V1-r1 (Founder attachment provenance — NOT Sol-verified)

- Plan ref / revision: MRPD-V1-r1
- Goal / signal id(s): MODEL_ROUTED_PRODUCT_DELIVERY_V1
- Planning Lead role + requested tier: Founder attachment §3 (Sol live CAPACITY_BLOCKED)
- Model evidence: requested Sol via Cursor CLI + Task → usage limit; tool-reported actual = N/A; status UNKNOWN/CAPACITY_BLOCKED
- CLI / config versions: Cursor agent 2026.09.15-d2fe57e; Codex 0.154.0; codex-route versioned copy
- Authorization basis: Founder instruction to execute attachment §3 in this session
- Implementation profile: Composer session (light worker for wiring only; not Luna)

## Goals / non-goals

- In scope: wire portable contract, resolver, AllTrue references, fixtures, evidence, PR
- Out of scope: new framework/DB/scheduler; production activation; skill reinstall; silent downgrade; H4B wake

## Nine facets

| Facet | Answer |
|---|---|
| Product & execution | Prove model-routed delivery under one-line In-App entry |
| Architecture | Reuse codex-route + portable docs; no new SoT |
| Platform & infrastructure | agent-start worktrees; no install --apply this run |
| Delivery & release | PR to portfolio-ops + AllTrue |
| Production reliability | N/A — no production mutation |
| Observability | probes.log + unittest |
| Security | no permission/billing changes |
| Governance | fail-closed; PLAN_REQUIRED preserved |
| Agent productivity / routing | dual-axis + handoff template |

## Worker return (this revision)

- Implemented docs/resolver/tests/AllTrue refs as listed in EVIDENCE.md
- Tests: 6 OK
- Open: live Sol→Luna handoff when quota restores
