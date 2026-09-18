# AUTHORITY_MAP

**Audit:** ENGINEERING_OS_DISCOVERY_V1 · 2026-09-18  
Detects multiple sources of truth. Prefer **one canonical authority** per state class; everything else is projection/reader.

Legend: **C** = canonical · **P** = projection · **R** = reader · **W** = writer · **Rec** = reconciliation

---

## 1. Multi-SoT findings (critical)

| State class | Competing authorities | Verdict |
|---|---|---|
| Company Goal / Run lifecycle | AllTrue `harness.sqlite` **and** portfolio `graph-control.sqlite` | **MULTIPLE SoT** — federate or pick one company Goal plane |
| Session / worktree binding | agent-control manifests (dual write: sessions/ + `.agent-session/`) | Single gateway OK; not Goal authority |
| Portfolio policy text | Hollow checkout AUTONOMY 2026-07-25 vs tip 2026-09-04 | **CONFLICTING POLICY SoT** |
| AllTrue task board | harness tasks table vs CURRENT_STATE vs DISPATCH_*.json vs FOUNDER_INBOX | Store C after cutover; JSON still used as Supervisor W |
| Production tip SHA | GitHub main tip vs Pi `deployment.json` | Distinct by design; Delivery Closure must reconcile |
| Graph autonomy readiness | live-dogfood-state.json vs completion-audit vs systemd | Ops JSON ≠ durable Run authority |

---

## 2. Major state → authority table

| State | Canonical authority | Projection | Readers | Writers | Reconciliation |
|---|---|---|---|---|---|
| AllTrue Program/Task status | `harness.sqlite` tasks/programs | `CURRENT_STATE.json` | Supervisor, CLI `status` | harness CLI / store APIs; demoted JSON writers | `project-state`; cutover demotion meta |
| GoalContract (AllTrue) | `goals` table (+ contracts in code) | plan review JSON | planner, dispatch | harness after H2 | subject_sha bind in PlanResult |
| DecisionReceipt | `decision_receipts` | FOUNDER_INBOX items | Founder gates | harness / Supervisor | empty live table — receipts often still JSON |
| Lease / fencing token | `leases` (CAS) | DISPATCH payloads | dispatch, worker_run | `cas_acquire/renew/release` | reclaim_stale; fencing compare |
| DispatchAttempt | `dispatch_attempts` | DISPATCH_*.json | Supervisor | `dispatch.py` | unique open-task index |
| WorkerRun | `worker_runs` | wake logs | launcher, observe | `worker_run.py` / agent-start | handoff observe; attach |
| Portfolio Goal/Run/Attempt | `graph-control.sqlite` | dogfood state JSON | scheduler CLI | durable_runtime / harness.py | event seq + state_version CAS |
| CanonicalEvent (portfolio) | `events` + ingest_key | — | observe/reducer | github_observe / ingest | ingest_key uniqueness |
| Effect / idempotent mutate | `effects` + idempotency_key | — | github_mutate | effect_journal | unique idempotency index (unused live) |
| Approval / human gate | `approvals` | FOUNDER_INBOX | observe | Founder / CLI | bound_head_sha |
| Session identity | agent-control session manifest | worktree `.agent-session/manifest.json` | workers | agent-start | validate-manifest |
| GitHub PR/CI truth | GitHub API / Actions | EI_SIGNAL_*.json, local caches | agents, observe | humans/bots via gh | manual H6; no H5 |
| Production deploy tip | Pi `deployment.json` / health | FOUNDER_ACTIVATION_REPORT_*, CONTROL_PLANE_CANONICAL_STATE | Delivery Closure | deploy workflow + Founder approve | exact-SHA compare |
| Delivery Closure queue | **de-facto** `DELIVERY_CLOSURE_QUEUE.json` | — | Founder/Supervisor | Supervisor ops | not in harness schema |
| Product BugReport | AllTrue DB `bug_reports*` | GH issues / ops dumps | Phase-A/C | app + workflows | product SOP; **not** harness |
| EI research knowledge | EI `data/research/cases/*.json` | reports/research/*.md | humans | ei pipelines | empty corpus |
| Sunrise outcomes | OUTCOME_LOG + admin outcomes API | BI reports | Founder | app + GHA | measured baseline |
| Model routing | `~/.codex/model-routing.toml` | — | Codex sessions | Founder/file edit | N/A (not Goal authority) |
| CubeLV UI/session | CubeLV product | — | Founder | CubeLV | must not write leases/deploy |
| Exo ticket/lock | `.exo/` local | — | exo CLI | exo | experiment only |

---

## 3. Intended target authority (reuse, do not rebuild)

| Layer | Keep as C | Demote / adapt |
|---|---|---|
| Product governance (tier, Phase-C, autonomy_gate, exact-SHA) | AllTrue governance scripts + deploy.yml | Never OSS-replace |
| GoalContract / PlanResult / EvidenceEnvelope / DecisionReceipt | AllTrue harness contracts | Graph Goal is parallel vocabulary — map, don’t fork semantics |
| Lease fencing CAS | AllTrue `leases` | Restate concurrency ≠ fence; keep compare |
| ExternalEvent wake durability | **ADAPT_RESTATE** (decision gate 2026-09-17) | Delete custom inbox once adapter proven |
| Worktree/session | agent-start | Keep |
| Fleet effect allowlist / portfolio graph | portfolio-ops agent_graph for **portfolio-ops project only** until federation contract exists | Do not enable graph-scheduler against AllTrue product Goals |
| Workers (Codex/Cursor/CubeLV) | never C | WorkerResult only |

---

## 4. Writer privilege risks

| Writer | Safe if | Unsafe if |
|---|---|---|
| Cursor/Codex chat | Emits WorkerResult + evidence refs | Mutates sqlite or claims ACCEPTED |
| Supervisor JSON files | Projection / handoff prompts | Treated as Task SoT after cutover |
| Hollow portfolio-ops tree | Never | Loaded as COMPANY_CONTROL_PLANE_ROOT |
| Restate (future) | Journals wake under AllTrue fence | Becomes Goal/lease authority |
| GitHub webhook | Ingest with ingest_key | Direct Task status mutate without Plan revalidate |

---

## 5. Reconciliation mechanisms that exist vs missing

| Mechanism | Status |
|---|---|
| harness `reconcile.py` / WorldObservation | CODE MERGED; not continuous tick |
| `project-state` JSON projection | RUNTIME |
| graph `durable_runtime` CAS | CODE; scheduler off |
| Delivery Closure vs deployment.json | MANUAL / JSON ops |
| CI conclusion → WorkerRun | MISSING |
| BugReport → Task | MISSING |
| Dual-plane Goal federation | MISSING (must not dual-enable) |
