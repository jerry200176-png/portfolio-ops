# MANUAL_INTERVENTION_MAP

**Audit:** ENGINEERING_OS_DISCOVERY_V1 · 2026-09-18  
Enumerates Founder (and Founder-as-Supervisor-relay) interventions that block “Goal-only” autonomy.

Frequency signals from `AUTONOMY_METRICS.json` (night 2026-09-16/17): `manual_wake_or_task_relaunches: 14`, `actionable_ci_not_auto_woken: 2`, `prod_approves: 0`, `founder_plan_reviews_required: 1`.

---

## 1. Copy / paste state

| Intervention | Where | Why still required | Evidence |
|---|---|---|---|
| Paste wake prompts between workers | `_wake_prompt_*.md`, chat | No H5 auto-wake; H4b e2e incomplete | wake logs; EI_ACTIONABLE_CI_* |
| Paste DISPATCH / plan JSON into sessions | `DISPATCH_*.json` → agent | No durable Goal→WorkerInvocation from FounderIntent alone | state/alltrue DISPATCH_* |
| Restate / UI spike decisions re-stated | FOUNDER_INBOX items | Receipts not driving auto-adapter start (`restate_gate1=FROZEN`) | FOUNDER_INBOX |
| Policy generation confusion | Hollow vs tip AUTONOMY | Agents may load wrong tree | hollow AUTONOMY vs tip |

---

## 2. Wake an agent / choose next task

| Intervention | Owner today | Automate via |
|---|---|---|
| Start Codex/Cursor on next READY task | Founder/Supervisor | H3 select + H4 dispatch + H4b start (close e2e) |
| Re-attach after crash/quota | Founder/Supervisor + dogfood scripts | Restate/Hatchet wait **or** harness tick + agent-start --attach |
| Pick among In-App vs TrueFit vs harness slices | Founder/Supervisor | Program WIP limits + planner (exists) + intake ranking (missing) |
| Resume graph RealCodex dogfood after quota | Cron intended; PIDs dead | Repair dogfood runtime OR stop claiming autonomy |

---

## 3. Restate context

| Intervention | Evidence |
|---|---|
| Re-explain MERGED≠ACCEPTED≠DEPLOYED ladder | GRAPH_TERMINOLOGY; repeated chat |
| Re-explain CubeLV is not host | Product Loop challenge docs; audits |
| Re-load CURRENT_STATE as if authoritative | Cutover demoted it; habits lag |
| Re-sync “what’s on Pi vs main” | CONTROL_PLANE_CANONICAL_STATE; Delivery Closure |

---

## 4. Inspect CI / assign workers / recover crashed work

| Intervention | Frequency | Gap ID |
|---|---|---|
| `gh` PR checks watch + paste failure to worker | High during delivery | H5 / ExternalEvent |
| Manually rebase when behind ruleset | Medium | observe+effect path partial |
| Supersede duplicate PRs | Observed (e.g. #3013) | planner/dispatch uniqueness not end-to-end |
| Kill/recover hung local processes | Medium | Shell ENOENT / du circuit breakers; hygiene |
| Rebuild Daan staging after migrate fail | Blocking staging verify | FOUNDER_INBOX daan-migrate; NO_NEW_MUTATION |

---

## 5. Merge / deploy / verify production

| Action | Policy (tip 2026-09-04) | Actual Founder load |
|---|---|---|
| Squash-merge R0–R2 | Agent operator after checks | Often still Founder/Supervisor habit; hollow policy says Founder-only |
| Production activation | Founder Environment (risk-based) | Required — correct safety boundary |
| Containment / PII / billing repair | Founder | Required |
| Runtime verify after deploy | Agent may do read-only; Founder often does | Delivery Closure not auto-closed |
| Flag activation (TrueFit) | Founder | Flags OFF despite MERGED code |

**Do not remove** Founder gates for irreversible / high-blast-radius production risk. Remove Founder from **relay** (wake, paste, ticket clerk), not from **safety**.

---

## 6. Synchronize GitHub / CubeLV / local state

| Sync | Manual? | Notes |
|---|---|---|
| GitHub PR status ↔ local WorkerRun | Yes | H6 manual |
| CubeLV issue observation | Often UNOBSERVED | Challenge client limitation |
| Local worktree hygiene | Semi (Phase1) | 13 removals; not continuous |
| Hollow checkout ↔ origin/main | Broken | autopilot exit 127 |
| graph-control canonical vs dogfood DBs | Confusing | thin canonical; rich dogfood |

---

## 7. Product / PM interventions

| Intervention | System |
|---|---|
| Triage in-app bugs into work | AllTrue (no harness ingest) |
| Approve In-App decision batches (#299 etc.) | Founder |
| RFID T3 / billing decisions | Founder |
| Enable EI automation var | Founder/ops |
| Sunrise autonomy leave STANDBY | Founder |
| Competitive research refresh | Manual one-shots |

---

## 8. Classification for removal priority

| Class | Examples | Remove? |
|---|---|---|
| **Relay** (should die) | Paste wake, CI babysit, next-task paste, JSON SoT habits | Yes — primary Goal of autonomy |
| **Clerk** (should die) | Intake from BugReport, duplicate PR supersede by hand | Yes — after wake works |
| **Safety** (keep) | Prod Environment, PII containment, billing/schema/T3 | Keep |
| **Ops debt** (fix once) | Hollow checkout, dead dogfood PIDs, stale CAPABILITY_REGISTRY | Fix as bounded Goals |

---

## 9. Open Founder inbox snapshot (2026-09-18)

- `open`: 7
- `plans_awaiting_review`: 1
- Sample items: Restate adopt spine (P2), AI Company UI spike (P2), Daan migrate failed (P1, blocks staging verified)

These are **decision packets**, not proof that automation is impossible — but frozen gates (`restate_gate1=FROZEN`) show decisions without execution wiring.
