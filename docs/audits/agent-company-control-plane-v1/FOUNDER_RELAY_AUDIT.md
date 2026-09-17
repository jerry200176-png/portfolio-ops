# FOUNDER_RELAY_AUDIT

**Audit:** `AGENT_COMPANY_CONTROL_PLANE_AUDIT_V1` · 2026-09-17  
Target: eliminate Founder *relay* (glue), preserve Founder *decisions* (genuine gates).

Classes:

- `AUTOMATABLE_DETERMINISTIC` — no LLM needed
- `AUTOMATABLE_AGENTIC` — agent OK with policy
- `FOUNDER_REQUIRED` — true Founder decision
- `UNNECESSARY_PROCESS` — stop doing this

---

## Relay inventory

| ID | Relay point | Evidence | Class | Notes |
|----|-------------|----------|-------|-------|
| FR-01 | Paste “worker finished / PR ready” between sessions | Operating plan; cycle JSON | AUTOMATABLE_DETERMINISTIC | WorkerRun completion event → Supervisor tick |
| FR-02 | Manual wake after CI failure | `EI_ACTIONABLE_CI_WORKER_NOT_AUTO_WOKEN.json` (#3024/#3023) | AUTOMATABLE_DETERMINISTIC | Webhook/Actions → owning WorkerRun resume |
| FR-03 | Tell agents which PR failed / which checks | Same EI + chat practice | AUTOMATABLE_DETERMINISTIC | Attach check run URLs to WorkItem |
| FR-04 | Restart/reattach coding CLI after stall | `EI_SUPERVISOR_TRANSPORT_STALL.json`; Cursor wakes | AUTOMATABLE_AGENTIC | Detect stall + `agent-start --attach` |
| FR-05 | Copy status across Supervisor sessions | CURRENT_STATE hand edits | AUTOMATABLE_DETERMINISTIC | Single store projection |
| FR-06 | Decide which worktree/branch maps to task | agent-start helps; still often remembered | AUTOMATABLE_DETERMINISTIC | WorkerRun.session_id authoritative |
| FR-07 | Ask for full status reconstruction | Frequent audit/reconcile goals | AUTOMATABLE_DETERMINISTIC | Reconciler CLI + Founder Console |
| FR-08 | Clean stale branches/worktrees | Hygiene Phase1; ~267 worktrees | AUTOMATABLE_DETERMINISTIC | Policy GC with dry-run + approve |
| FR-09 | Notice stuck CI / stale PRs | Manual `gh` / Supervisor | AUTOMATABLE_DETERMINISTIC | Watchdog on open WorkerRuns |
| FR-10 | Reconcile GitHub vs local JSON | Dual SoT | AUTOMATABLE_DETERMINISTIC | GitHub observe adapters already in agent_graph |
| FR-11 | Translate In-App feedback → GH tasks | Product BugReport ≠ CP intake | AUTOMATABLE_AGENTIC | Intake adapter + dedup |
| FR-12 | Repeat context/prompts each wake | Wake prompt markdown files | AUTOMATABLE_DETERMINISTIC | Durable WorkItem + resume packet |
| FR-13 | Route work Pi / Daan / CubeLV as “machines” | CubeLV is an agent, not a host | UNNECESSARY_PROCESS | Fix mental model; schedule by capability labels |
| FR-14 | Remember parked work (#3016,#2981,billing) | CURRENT_STATE.parked | AUTOMATABLE_DETERMINISTIC | WorkItem states |
| FR-15 | Daan Docker interactive session | FOUNDER_INTERACTIVE_DOCKER; migrate incident | FOUNDER_REQUIRED *(today)* → later AUTOMATABLE_DETERMINISTIC | Needs sudo/docker group redesign first |
| FR-16 | Production Environment deploy approval | deploy.yml; activation reports | FOUNDER_REQUIRED | Keep |
| FR-17 | Product architecture Plan (#299 auth) | FOUNDER_INBOX `esc_inapp_299_plan_review` | FOUNDER_REQUIRED | Keep |
| FR-18 | T3 RFID merge GO | `esc_rfid1_schema_merge` | FOUNDER_REQUIRED | Keep |
| FR-19 | Production data repair (#302/#303) | FOUNDER_INBOX billing items | FOUNDER_REQUIRED | Keep |
| FR-20 | TrueFit flag ON / billing / identity | Parked; activation reports | FOUNDER_REQUIRED | Keep |
| FR-21 | Restate production adoption GO | FOUNDER_INBOX + ADOPTION_STATE | FOUNDER_REQUIRED | Keep until Gate-1 proof |
| FR-22 | Approve agent-finish removals | agent-finish `--approve-removal` | FOUNDER_REQUIRED *(batch)* or AUTOMATABLE_DETERMINISTIC with policy | Prefer policy allowlist for clean linked PRs |
| FR-23 | Manually run graph-scheduler / dogfood units | systemd disabled | UNNECESSARY_PROCESS *or* AUTOMATABLE | Either delete dead units or enable with ownership |
| FR-24 | Relabel CubeLV as compute node | Docs/chat confusion | UNNECESSARY_PROCESS | Document once; stop |
| FR-25 | Staging migrate remediation after vendor crash | MIGRATE_INCIDENT_RECONCILE | FOUNDER_REQUIRED | Safety boundary this cycle |

---

## Summary counts

| Class | Count (this audit) |
|-------|--------------------|
| AUTOMATABLE_DETERMINISTIC | 12 |
| AUTOMATABLE_AGENTIC | 2 |
| FOUNDER_REQUIRED | 9 |
| UNNECESSARY_PROCESS | 2 |

**Open Founder inbox (actionable-ish):** 4 of 7 listed items still open (RFID, #299 plan, billing 302/303).

---

## Highest-ROI relay eliminations (ordered)

1. **FR-02/03** — CI → auto-wake owning worker (closes the most frequent paste loop).
2. **FR-01/05/06/12** — WorkerRun + single SoT (ends session archaeology).
3. **FR-08/09/10** — Reconcile + GC watchdogs (ends Founder as janitor).
4. **FR-11** — In-App → WorkItem intake (ends Founder as ticket clerk).
5. Keep **FR-16–20** as true Founder Console actions (APPROVE/REJECT), not chat glue.

---

## Anti-goal

Do **not** “optimize prompts” so Founder can relay faster.  
Do **replace relay with events + durable identity + policy**.
