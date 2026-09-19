# GAP_BACKLOG

**Audit:** `AGENT_COMPANY_CONTROL_PLANE_AUDIT_V1` · 2026-09-17  
Priorities: P0 prevents autonomy · P1 cuts Founder relay · P2 throughput/quality/obs · P3 scale-not-needed  
**Critical path:** G-P0-01 → G-P0-02 → G-P1-01 → G-P1-02 → G-P1-03 → Console later.

---

## P0 — prevents reliable autonomous operation

### G-P0-01 Harness store authority cutover
| Field | Content |
|-------|---------|
| ID | G-P0-01 |
| problem | MERGED harness schema v4 (WorkerRun/DispatchAttempt) but live `harness.sqlite` is schema v1; JSON files remain de-facto SoT |
| current evidence | `store.py SCHEMA_VERSION=4`; sqlite `meta schema_version=1`; no `worker_runs` table; `CURRENT_STATE.json` |
| user/business impact | Platform claims false; resume/adopt cannot be authoritative; audits forever |
| failure mode | Duplicate dispatches; lost ownership after Supervisor restart |
| frequency | Continuous |
| manual Founder burden | High (status reconstruction, wake paste) |
| risk | High — fake automation |
| external precedent | Temporal/Restate: store is authority; UI/clients are projections |
| recommended solution | Migrate live DB to v4; make reconciler write store first; demote JSON to projection |
| build/adopt/adapt | HARDEN (build) |
| dependencies | None |
| estimated complexity | M |
| reversibility | High (backup sqlite) |
| priority | P0 |

### G-P0-02 CI / external event → WorkerRun auto-wake
| Field | Content |
|-------|---------|
| ID | G-P0-02 |
| problem | Actionable CI failures do not return to owning worker |
| current evidence | `EI_ACTIONABLE_CI_WORKER_NOT_AUTO_WOKEN.json` (#3024/#3023); Restate PoC local only |
| user/business impact | Throughput collapse; Founder/Supervisor paste loop |
| failure mode | Stale failed PRs; silent stalls |
| frequency | Multiple per day during active delivery |
| manual Founder burden | High |
| risk | High for autonomy goal |
| external precedent | Restate awakeables; Temporal signals; OpenHands Automation triggers |
| recommended solution | Restate Gate-1 adapter on real WorkerRun + webhook/Actions ingest; keep AllTrue fencing |
| build/adopt/adapt | ADAPT_EXTERNAL (Restate) + HARDEN harness |
| dependencies | G-P0-01 |
| estimated complexity | M–L |
| reversibility | High (adapter feature-flag) |
| priority | P0 |

### G-P0-03 Single reconciler tick (no dual schedulers)
| Field | Content |
|-------|---------|
| ID | G-P0-03 |
| problem | No durable Supervisor loop; graph-scheduler exists but disabled; chat is the loop |
| current evidence | systemd `graph-scheduler` inactive; SUPERVISOR_CYCLE JSON; H7 PARTIAL |
| user/business impact | Autonomy dies when Cursor session ends |
| failure mode | Drift between GitHub and local state |
| frequency | Every session boundary |
| manual Founder burden | Medium–High |
| risk | High |
| external precedent | Temporal worker processes; Restate deployments |
| recommended solution | One supervised tick owning harness reconcile+wake drain; do not enable agent_graph scheduler in parallel |
| build/adopt/adapt | HARDEN |
| dependencies | G-P0-01 |
| estimated complexity | M |
| reversibility | High |
| priority | P0 |

---

## P1 — materially reduces Founder relay

### G-P1-01 Canonical intake + dedup
| Field | Content |
|-------|---------|
| ID | G-P1-01 |
| problem | In-App / Issues / incidents enter via Founder/Supervisor memory |
| current evidence | BugReport product vs FOUNDER_INBOX split; no WorkItem intake table live |
| user/business impact | Lost/duplicated work; Founder as ticket clerk |
| failure mode | Double implementation; dropped feedback |
| frequency | Weekly+ |
| manual Founder burden | High |
| risk | Medium |
| external precedent | Issue trackers + idempotent event APIs |
| recommended solution | Intake adapters → WorkItem with dedupe keys |
| build/adopt/adapt | HARDEN |
| dependencies | G-P0-01 |
| estimated complexity | M |
| reversibility | High |
| priority | P1 |

### G-P1-02 Stale PR/CI/worktree reconciler + GC
| Field | Content |
|-------|---------|
| ID | G-P1-02 |
| problem | Founder/Supervisor notice stuck CI, stale PRs, ~267 worktrees |
| current evidence | agent-finish manual approve; hygiene Phase1 ad-hoc; sessions ~1011 |
| user/business impact | Disk/noise; wrong-branch edits |
| failure mode | Work on abandoned trees |
| frequency | Continuous accumulation |
| manual Founder burden | Medium |
| risk | Medium |
| external precedent | Sweeper jobs; OpenHands run history GC patterns |
| recommended solution | Policy GC candidates + batch Founder/policy approve |
| build/adopt/adapt | HARDEN (reuse agent-finish) |
| dependencies | G-P0-03 |
| estimated complexity | M |
| reversibility | Medium (need dry-run) |
| priority | P1 |

### G-P1-03 Delivery closure automation (staging evidence bind)
| Field | Content |
|-------|---------|
| ID | G-P1-03 |
| problem | MERGED work waits Founder/Supervisor to notice staging/runtime evidence (#296 pattern) |
| current evidence | DELIVERY_CLOSURE_QUEUE; CURRENT_STATE Worker B wait |
| user/business impact | Closure lag; WIP soft-lock |
| failure mode | Forever-open delivery |
| frequency | Per feature |
| manual Founder burden | Medium |
| risk | Medium |
| external precedent | Deploy observers; wait-github-deploy already exists |
| recommended solution | Bind WorkItem acceptance checklist to deterministic probes |
| build/adopt/adapt | HARDEN |
| dependencies | Daan recovery (external); G-P0-01 |
| estimated complexity | M |
| reversibility | High |
| priority | P1 |

### G-P1-04 Demote / park dual agent_graph control plane
| Field | Content |
|-------|---------|
| ID | G-P1-04 |
| problem | Competing Attempt/Run scheduler + docs imply autonomy |
| current evidence | agent_graph MERGED; scheduler disabled; dogfood sqlite |
| user/business impact | Confusion; wasted dogfood cycles |
| failure mode | Accidental dual dispatch if enabled |
| frequency | Ongoing cognitive load |
| manual Founder burden | Low–Medium |
| risk | Medium if enabled |
| external precedent | One orchestrator per org |
| recommended solution | Extract github/deploy adapters; document agent_graph as library/dogfood only; delete or archive enabled units |
| build/adopt/adapt | ADAPT + DELETE false automation |
| dependencies | G-P0-03 |
| estimated complexity | S–M |
| reversibility | High |
| priority | P1 |

---

## P2 — throughput / quality / observability

### G-P2-01 Founder Console MVP
| Field | Content |
|-------|---------|
| ID | G-P2-01 |
| problem | Founder operates via prompts |
| current evidence | AI_COMPANY_UI PLAN_ONLY |
| impact | Relay persists even after backend fixed |
| failure mode | UI on empty SoT |
| frequency | Daily |
| Founder burden | High until built |
| risk | Medium (premature UI) |
| precedent | OpenHands Canvas; Restate UI |
| solution | Spec in CONTROL_PLANE_UI_SPEC; implement after P0 |
| build/adopt/adapt | ADAPT Restate UI + custom |
| dependencies | G-P0-01..03 |
| complexity | L |
| reversibility | High |
| priority | P2 |

### G-P2-02 Cost/trace telemetry
| Field | Content |
|-------|---------|
| ID | G-P2-02 |
| problem | No token/cost store; autonomy metrics inferred ad-hoc |
| evidence | EI0 MISSING; AUTONOMY_METRICS.json handish |
| impact | Cannot budget workers |
| solution | Langfuse or OTel GenAI attrs |
| build/adopt/adapt | ADAPT_EXTERNAL |
| dependencies | WorkerRun identity |
| complexity | M |
| priority | P2 |

### G-P2-03 Stall detector / transport recovery
| Field | Content |
|-------|---------|
| ID | G-P2-03 |
| problem | Supervisor transport stalls need human wake |
| evidence | EI_SUPERVISOR_TRANSPORT_STALL |
| solution | Heartbeat + auto --attach |
| build/adopt/adapt | HARDEN |
| dependencies | G-P0-01 |
| complexity | M |
| priority | P2 |

---

## P3 — scale capability not currently required (“cosplay”)

| ID | Item | Why not now |
|----|------|-------------|
| G-P3-01 | Kubernetes / Nomad / agent-sandbox fleet | 3 roles; worktrees enough |
| G-P3-02 | Fairness/capacity multi-tenant scheduler | Single-operator company |
| G-P3-03 | A2A mesh as primary bus | Need WorkItem SoT first |
| G-P3-04 | Full deterministic replay of all LLM steps | Expensive; wake-path durability sufficient |
| G-P3-05 | Replace agent-control with SWE-ReX platform | Isolation already works |
| G-P3-06 | LangGraph company OS | Wrong layer; graph overengineering already observed |

---

## Explicit non-goals (big-company cosplay)

Do **not** build: multi-region control planes, service mesh for agents, full eval platforms before intake, second orchestrator “for redundancy,” CubeLV-as-host inventory, always-on staging farms on 3.4 GiB hosts.
