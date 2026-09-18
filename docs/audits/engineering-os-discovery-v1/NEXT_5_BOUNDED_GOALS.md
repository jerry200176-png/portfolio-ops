# NEXT_5_BOUNDED_GOALS

**Audit:** ENGINEERING_OS_DISCOVERY_V1 · 2026-09-18  
Ordered for **maximum Founder-relay removal** under reuse constraints.  
Prior audit G-P0-01 (harness store cutover) is **done** (schema v4 live) — do not re-open as primary.

---

## Goal 1 — CONTROL_PLANE_CHECKOUT_INTEGRITY

| Field | Content |
|---|---|
| **Outcome** | `COMPANY_CONTROL_PLANE_ROOT` / documented “canonical” portfolio-ops checkout resolves to a tip tree with `AGENT_BOOTSTRAP.md`, `AUTONOMY_POLICY` (2026-09 operator), `scripts/`, and `agent_graph/` sources. Governance autopilot no longer fails exit 127 on missing script. |
| **Why now** | Agents and systemd still point at a hollow exo checkout; dual AUTONOMY generations create silent policy violations — autonomy without correct contracts is unsafe. |
| **Dependencies** | None |
| **Scope** | Repair/replace hollow `/home/jerry/workspace/portfolio-ops` pointer (worktree from bare or documented symlink to tip); fix autopilot unit paths; update local AGENTS pointer if needed; verify `agent-start` preflight against tip. |
| **Non-scope** | Graph scheduler enablement; Restate; product features; rewriting AUTONOMY policy content |
| **Risk** | Medium — wrong cutover could confuse sessions mid-flight |
| **Evidence required** | Autopilot timer success; file presence list; `agent-start portfolio-ops … --dry-run` PASS on tip contracts; no 2026-07-25 “Founder must merge” loaded as fleet default |
| **Founder gates** | Approve which path becomes the local canonical checkout (replace vs symlink vs retire directory name) |
| **Stop conditions** | Tip contracts load; autopilot green once; do not cascade into scheduler enable |

---

## Goal 2 — H4B_E2E_WAKE_ACCEPTANCE

| Field | Content |
|---|---|
| **Outcome** | One real AllTrue PlanResult → DispatchAttempt → `agent-start --attach` → WorkerRun handoff completes **without** Supervisor paste; acceptance artifact flips H4/H4b from PARTIAL/NOT_ACCEPTED to OPERATIONALLY_ACCEPTED for the e2e path. |
| **Why now** | Code MERGED (#3022/#3025) and cutover dogfood exists, but product wake still relies on paste — blocks H5 value. |
| **Dependencies** | Goal 1 recommended (correct agent-start/contracts); harness v4 already live |
| **Scope** | Dogfood on a disposable/low-risk task; close observe_worker_handoff gaps; record acceptance JSON; fix only blockers proven by the e2e |
| **Non-scope** | Restate production; CI webhook; UI; new schema major version |
| **Risk** | Low–Medium (local orchestration) |
| **Evidence required** | WorkerRun rows + session manifest + PR link; no `_wake_prompt_*` in the happy path; tests green; acceptance explicitly states OPERATIONALLY_ACCEPTED or lists residual gaps |
| **Founder gates** | None for R0–R2 dogfood; Founder only if touching production activation |
| **Stop conditions** | First green e2e OR two distinct blockers documented with tickets — no scope expansion into H5 |

---

## Goal 3 — EXTERNAL_EVENT_WAKE_ADAPTER_V1

| Field | Content |
|---|---|
| **Outcome** | Actionable CI failure (or equivalent GitHub webhook) wakes the owning WorkerRun via **ADAPT_RESTATE** (or thinner durable queue if Restate blocked) **under AllTrue lease fencing**; `EI_ACTIONABLE_CI_WORKER_NOT_AUTO_WOKEN` class incidents drop to zero on the dogfood PR set. |
| **Why now** | Highest measured Founder/Supervisor relay (`manual_wake_or_task_relaunches`); durability gate already decided ADAPT_RESTATE; PoC exists; `restate_gate1=FROZEN` awaiting execution wiring. |
| **Dependencies** | Goal 2 (stable WorkerRun identity); Founder inbox decision on Restate adopt (or explicit defer with alternate) |
| **Scope** | Thin adapter: ExternalEvent ingest → signal/awakeable → revalidate PlanResult + fence → `agent-start --attach`; feature-flagged; no authority transfer of Goal/lease to Restate |
| **Non-scope** | Replace harness store; enable graph-scheduler; AI Company UI; multi-region Restate |
| **Risk** | Medium — duplicate wakes if fence buggy |
| **Evidence required** | Duplicate-delivery test; stale fencing test; process restart test; real CI dogfood PR auto-wake log; production_adoption still false until separate gate |
| **Founder gates** | Approve unfreeze `restate_gate1` / adapter enable on Ubuntu host; no Pi production change |
| **Stop conditions** | Adapter dogfood green OR INSUFFICIENT_EVIDENCE with measured failure — do not rewrite GoalContract |

---

## Goal 4 — SINGLE_DURABLE_RECONCILE_TICK

| Field | Content |
|---|---|
| **Outcome** | One supervised durable tick owns harness reconcile + wake-drain so Cursor session death does not freeze the loop; **graph-scheduler remains disabled** for AllTrue product Goals. |
| **Why now** | H7 PARTIAL; chat is the loop; enabling two schedulers was previously flagged unsafe. |
| **Dependencies** | Goal 3 preferred (something to drain); Goal 2 minimum |
| **Scope** | systemd user unit **or** Restate scheduled invocation calling existing `scripts.harness` reconcile/wake APIs; heartbeat; fail-closed; metrics counter for tick success |
| **Non-scope** | portfolio-ops graph autonomous V1 declared done; multi-host; new DB |
| **Risk** | Medium — runaway ticks / duplicate dispatch if uniqueness regresses |
| **Evidence required** | Kill session → tick continues; no double open DispatchAttempt; machine_reboot proof updated from UNPROVEN if claimed |
| **Founder gates** | Approve enabling the single unit on the Ubuntu host |
| **Stop conditions** | Tick proven on reboot once; do not also enable `graph-scheduler.service` |

---

## Goal 5 — CANONICAL_INTAKE_WORKITEM_V1

| Field | Content |
|---|---|
| **Outcome** | In-app BugReport (and/or labeled GH issue) creates a deduped harness Task + GoalContract stub without Founder copy/paste; FOUNDER_INBOX only receives true DecisionPackets. |
| **Why now** | Product intake already PRODUCTION_VERIFIED; missing bridge is pure Founder-clerk load; planning/execution primitives exist. |
| **Dependencies** | Goals 2–4 for autonomous follow-through; can prototype ingest earlier but value limited without wake |
| **Scope** | One intake source (prefer BugReport Phase-A output); idempotent upsert; map to `alltrue-inapp` program; escalate policy-violating items |
| **Non-scope** | Full PM suite; EI market research; Sunrise; auto Phase-C; auto production |
| **Risk** | Medium — bad classification → wrong auto-exec envelope |
| **Evidence required** | Two synthetic + one real bug → single Task; duplicate suppressed; no billing/auth auto-exec; audit log |
| **Founder gates** | Approve intake source + auto-exec allowlist unchanged (fail closed) |
| **Stop conditions** | One source live; do not expand to email/Gmail/EI in same Goal |

---

## Deferred (explicitly not in NEXT_5)

| Item | Why deferred |
|---|---|
| OUTCOME_LEARNING_ALLTRUE_V1 | Needs stable delivery close + metrics definition; Sunrise already has pattern to copy later |
| FLEET_GOAL_FEDERATION | Only if portfolio graph must drive AllTrue — avoid until single-tick proven |
| AI Company UI | Relay removal does not require UI first |
| EI_AUTOMATION_ENABLED flip | Empty corpus / policy; not on Founder-relay critical path |
| TrueFit flag RUNTIME enable | Product decision + Founder activation — safety class |

---

## Sequencing diagram

```
[1] Checkout integrity
      → [2] H4b e2e acceptance
            → [3] ExternalEvent wake (ADAPT_RESTATE)
                  → [4] Single durable tick
                        → [5] Canonical intake
                              → (later) Outcome learning
```
