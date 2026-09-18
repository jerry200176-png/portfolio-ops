# CAPABILITY_MATRIX

**Audit:** ENGINEERING_OS_DISCOVERY_V1 · 2026-09-18  

Classification: **IMPLEMENTED** | **PARTIAL** | **MISSING** | **DUPLICATED** | **OBSOLETE** | **UNKNOWN**

Maturity labels (evidence-gated): DESIGNED → CODE_WRITTEN → TESTED → MERGED → RUNTIME_ENABLED → PRODUCTION_VERIFIED → OPERATIONALLY_ACCEPTED.

Do **not** treat DOCUMENT-only as IMPLEMENTED.

---

## Portfolio capabilities (required set)

| Capability | Class | Maturity (best evidence) | Notes |
|---|---|---|---|
| Product intake | PARTIAL | BugReport PRODUCTION_VERIFIED; harness ingest MISSING | AllTrue SOP + Phase-A/C; no BugReport→Task bridge |
| PM / discovery | PARTIAL | Manual + Product Loop dogfood | Founder/Supervisor prioritize; Sunrise prioritize.sh exists |
| Research | PARTIAL | EI CODE/TESTED; schedules OFF; corpus empty | Competitive audits one-shot |
| Prioritization | PARTIAL | portfolio-ops ICE docs; Sunrise orchestrator STANDBY | No EI1 planner feedback |
| Architecture | PARTIAL | ADRs/spikes/audits MERGED as docs | Dual-plane conflict unresolved |
| Planning | IMPLEMENTED* | H3 MERGED + OPERATIONALLY_ACCEPTED (AllTrue) | *Product-domain only; not fleet Goal planner |
| Execution | PARTIAL | H4/H4b MERGED; e2e wake PARTIAL; graph dogfood stalled | agent-start RUNTIME_ENABLED |
| Code review | PARTIAL | GH checks + CubeLV challenge + human | No durable review WorkItem authority |
| Testing | IMPLEMENTED | Product CI + harness unit tests MERGED | Local heavy-gate discipline |
| Security | PARTIAL | autonomy_gate, Phase-C allowlist, SEC issues | Containment still Founder-heavy |
| CI | IMPLEMENTED | GitHub Actions on products | Wake-back MISSING |
| Release | PARTIAL | Release notes / silent_ship discipline | MERGED≠ACCEPTED≠DEPLOYED ladder |
| Deployment | PARTIAL | exact-SHA deploy.yml PRODUCTION path | Founder Environment gate; tip lag common |
| Runtime verification | PARTIAL | health/version/deployment.json + acceptance workflows | Many items RUNTIME_VERIFIED=false |
| Observability | PARTIAL | Product health + scorecards; no EI0 telemetry store | Sentry optional/partial |
| SRE / incident | PARTIAL | SOPs + FOUNDER_INBOX escalations | No automated page→WorkItem |
| Outcome measurement | PARTIAL | Sunrise OUTCOME_LOG RUNTIME_ENABLED; AllTrue weak | Phase-C close ≠ outcome learning |
| Platform engineering | PARTIAL | agent-control + worktrees strong | Hollow checkout / dual SoT weak |
| Agent productivity | PARTIAL | AUTONOMY_METRICS JSON; H4/H5 targets | 14 manual wakes in one night window |
| Governance | IMPLEMENTED* | Contracts + CI rulesets exist | *Conflicting policy generations on disk |
| Durable orchestration | PARTIAL | harness v4 RUNTIME; graph CODE; Restate ADAPT decided not adopted | No production Restate |
| Recovery / reconciliation | PARTIAL | cutover dogfood; reclaim leases; hygiene Phase1 | machine_reboot UNPROVEN; dual reconciler risk |
| Knowledge / context management | PARTIAL | FOUNDER_INBOX, CURRENT_STATE projection, docs | Chat memory still primary for continuity |

\*IMPLEMENTED means “exists and works in its declared domain,” not “closes the Founder-Goal autonomy loop.”

---

## Control-plane slice matrix (H-ladder + fleet)

| Slice | Class | Maturity | Evidence |
|---|---|---|---|
| H0–H1 Task/Program SM | IMPLEMENTED | OPERATIONALLY_ACCEPTED | #2977; gap matrix; tests |
| H2 GoalContract + CAS lease/fencing | IMPLEMENTED | OPERATIONALLY_ACCEPTED | H2_CORRECTNESS_ACCEPTANCE; leases live=9 |
| H3 Planner | IMPLEMENTED | OPERATIONALLY_ACCEPTED | H3_ACCEPTANCE; #3014 |
| H4 DispatchAttempt | PARTIAL | MERGED + TESTED; not OA | #3022; H4_IMPL_FINALIZED NOT_ACCEPTED |
| H4b WorkerRun start/attach | PARTIAL | MERGED + RUNTIME dogfood; e2e product wake incomplete | #3025; cutover wr; ARCHITECTURE PARTIAL |
| Store authority cutover | PARTIAL | RUNTIME_ENABLED; OA contested | sqlite OA=true vs HARNESS_STATUS pending; reboot UNPROVEN |
| H5 CI → owning worker wake | MISSING | DESIGNED + Restate PoC TESTED | EI_ACTIONABLE_CI_WORKER_NOT_AUTO_WOKEN; restate_gate1=FROZEN |
| H6 ExternalObserver | PARTIAL | Manual RUNTIME | gh/WebFetch; no harness loop |
| H7 Durable supervisor tick | PARTIAL | Cursor session + JSON | graph-scheduler disabled |
| H8 Recovery/GC | PARTIAL | Hygiene Phase1 DEGRADED accepted | no ACCEPTED→finalize automation |
| CanonicalEvent inbox (harness) | MISSING | DESIGNED only | type absent in scripts/harness |
| CanonicalEvent (graph-control) | PARTIAL | CODE_WRITTEN; thin live DB | durable_models; 1 event row |
| Effect journal / idempotency | PARTIAL | CODE on graph; unused live | effects=0; AllTrue DeliveryClosure JSON |
| WorkerInvocation / WorkerResult | DUPLICATED | CODE both planes | harness WorkerRun vs graph WorkerResult |
| Goal / Run / Attempt | DUPLICATED | Both planes | Different schemas/semantics |
| Restate durable wake | PARTIAL | PoC + durability gate ADAPT_RESTATE | production_adoption=false |
| agent-start gateway | IMPLEMENTED | RUNTIME_ENABLED | H4b attach path |
| Portfolio autonomous scheduler | PARTIAL | CODE_WRITTEN; not RUNTIME_ENABLED | dogfood quota_wait; autonomy NO |
| EI telemetry/feedback | MISSING | — | gap matrix EI0/EI1 |
| ExoProtocol fleet authority | OBSOLETE* | experiment-only | *as authority; experiment locks OK |
| company-os broad autonomy grant | OBSOLETE | revoked 2026-07-25 | historical |
| Hollow portfolio-ops checkout as SoT | OBSOLETE / CONFLICT | breaks autopilot | scripts missing |
| CAPABILITY_REGISTRY (2026-07-19) | OBSOLETE | STALE | does not list harness/graph |
| CubeLV as host/orchestrator | OBSOLETE myth | DOC + audits | challenge client only |

---

## Product-domain loops

| Loop | Class | Maturity |
|---|---|---|
| AllTrue BugReport → GH → Phase-C | IMPLEMENTED | PRODUCTION_VERIFIED (product) |
| AllTrue BugReport → harness Task | MISSING | DESIGNED in policy/YAML |
| TrueFit S6 continuum | PARTIAL | MERGED; flags OFF → not RUNTIME_ENABLED |
| Sunrise Product Improvement + OUTCOME_LOG | PARTIAL | RUNTIME_ENABLED measurement; autonomy STANDBY |
| EI research candidates → backlog | MISSING | empty reports/candidates |
| Delivery Closure (exact-SHA) | PARTIAL | JSON RUNTIME ops; Founder activate |

---

## Duplication / conflict summary

| Pair | Risk |
|---|---|
| `harness.sqlite` vs `graph-control.sqlite` | Dual Goal/Run/Attempt authorities; unsafe to enable both schedulers |
| Hollow AUTONOMY (no-merge) vs tip AUTONOMY (Agent merges) | Agents loading wrong tree violate policy |
| CURRENT_STATE / DISPATCH JSON vs harness store | Mostly demoted; some ops JSON still Supervisor SoT |
| EI_* JSON under state/alltrue vs engineering-intelligence repo | Naming collision; different systems |
| `AllTrue_System-clean` vs bare `main` | Stale checkout traps agents |

---

## Overall verdict on “Founder only provides Goal”

| Loop stage | Class |
|---|---|
| Product Discovery | PARTIAL / MISSING automation |
| Planning | IMPLEMENTED (AllTrue H3) |
| Engineering | PARTIAL |
| Review | PARTIAL |
| Delivery | PARTIAL |
| Runtime Verification | PARTIAL |
| Outcome Learning | MISSING (AllTrue) / PARTIAL (Sunrise) |

**Distance:** strong product-domain orchestration primitives exist; the **closed autonomous loop does not**. Largest missing links are external-event wake, durable tick, canonical intake, and outcome feedback — not another planning framework.
