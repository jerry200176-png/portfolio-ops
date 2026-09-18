# OPEN_SWE_REUSE_SPIKE

**Status:** RESEARCH COMPLETE — recommendation only; no install, no scheduler enable, no production mutation  
**Date:** 2026-09-18  
**Upstream tip inspected:** `langchain-ai/open-swe` @ `b73659fb0a2cbe77892348f37910fd607eea2f44` (main, 2026-09-18)  
**Local evidence clone (read-only):** `/home/jerry/workspace/state/alltrue/spikes/open-swe-reuse-20260918/open-swe`  
**Related deferred Goal:** `H4B_E2E_AUTONOMY_ACCEPTANCE` → `goals/harness/H4B-E2E/GOAL.json`  
**Prior related decisions:** `OSS_CONTROL_PLANE_ADOPT_OR_BUILD_SPIKE.md` (ADAPT_RESTATE for wake); durability gate `ADAPT_RESTATE`

---

## 1. Executive verdict

**Do not adopt Open SWE as the control plane.** It is a strong **LangGraph + Deep Agents software-factory product** (MIT) whose best ideas for us are **patterns**, not a wholesale replacement of AllTrue `harness.sqlite` / GoalContract / CAS fencing / exact-SHA governance.

| Local need | Open SWE fit | Classification |
|---|---|---|
| H4b handoff / attach | Different runtime (LangGraph thread ≠ agent-start WorkerRun) | **ADAPT_PATTERN** (deterministic thread/run identity, interrupt-resume) |
| H5 CI → owning worker | **Strongest match:** `/baby-sit` + CI webhook + cron fallback | **ADAPT_PATTERN** (algorithm); durable spine stays **ADAPT_RESTATE** |
| H7 durable tick | Scheduler graph + `reconcile_stale_runs` | **ADAPT_PATTERN**; do **not** enable Open SWE or portfolio `graph-scheduler` as AllTrue SoT |
| Canonical intake | GitHub/Slack/Linear → deterministic thread | **ADAPT_PATTERN** for routing IDs; intake content stays AllTrue BugReport/GH |
| CI babysitting | `agent/baby_sit.py` | **ADAPT_PATTERN** / selective **REFERENCE_ONLY** code shape |
| Review separation | Separate read-only reviewer graph | **ADAPT_PATTERN** (CubeLV/challenge already similar) |
| Workspace/thread recovery | Per-thread sandbox + sync durability + stale cancel | **ADAPT_PATTERN**; map to agent-start worktree + WorkerRun |
| Provider abstraction | Deep Agents / multi-model inside LangGraph | **REJECT** as authority; keep Codex/Cursor as replaceable workers via agent-start |

**Bottom line:** Keep proven local contracts. Steal **routing, babysit, stale-run, and reviewer-boundary patterns**. Keep **ADAPT_RESTATE** for ExternalEvent durability. Do **not** install Open SWE into production or replace H4B with a LangGraph rewrite.

---

## 2. Current local gaps being compared

From `ENGINEERING_OS_DISCOVERY_V1` + live state (2026-09-18):

| Gap | Local maturity |
|---|---|
| H4b e2e Plan→Dispatch→WorkerRun→attach→handoff without paste | PARTIAL (code MERGED; acceptance deferred — Goal blocked on Codex capacity) |
| H5 ExternalEvent→WorkerRun wake | MISSING (`restate_gate1=FROZEN`) |
| H7 durable reconcile tick | PARTIAL (chat is loop; `graph-scheduler` disabled) |
| Canonical intake BugReport→Task | MISSING |
| CI babysitting | Manual (`AUTONOMY_METRICS.manual_wake_or_task_relaunches`) |
| Review separation | PARTIAL (CI + CubeLV challenge; not harness-owned) |
| Workspace/thread recovery | PARTIAL (agent-start `--attach`; cutover dogfood; machine_reboot UNPROVEN) |
| Provider abstraction | agent-start CLI flags; no ACP production path |

**Must not replace:** GoalContract, PlanResult world-bind, DispatchAttempt, WorkerRun, CAS leases/fencing, autonomy_gate, exact-SHA deploy, Phase-C.

---

## 3. Open SWE architecture summary

Open SWE = **software factory** on **Deep Agents** (harness) + **LangGraph** (durable runs/threads) + FastAPI webhooks/dashboard.

**Graphs** (`langgraph.json`): `agent`, `reviewer`, `analyzer`, `chat`, `scheduler`.

**Core loop (README):** Issues/conversations/PRs/schedules → plan/investigate → sandbox implement → PR → review/CI/feedback → follow-up on **same thread**.

**Dispatch contract** (`agent/dispatch.py`):
- Single `dispatch_agent_run` for Slack/Linear/GitHub/dashboard
- `durability="sync"` + `multitask_strategy="interrupt"` (follow-ups interrupt & resume)
- Optional completion webhook (fail-closed; no loopback by default)
- Deterministic thread IDs so follow-ups route to the originating run

**CI babysit** (`agent/baby_sit.py`):
- Opt-in watches; GitHub CI webhook immediate eval; `*/10` cron fallback
- Lock via dedicated thread id; dedupe delivery/dispatch keys; flake rerun caps
- On failure: `dispatch_agent_run` back to **originating** `thread_id`

**Scheduler** (`agent/scheduler.py`):
- Thin fan-out: baby_sit, reconcile, workspace refresh, scheduled agent runs, costs
- `reconcile_stale_runs` cancels stuck `pending` runs on busy threads

**Safety surfaces:** GitHub App install boundaries, org/repo allowlists, read-only reviewer/chat graphs, human approval before workflow-file pushes, credentials in server/proxy not agent prose.

**Not our model:** LangGraph/LangSmith as SoT; cloud sandboxes as worktree authority; Open SWE dashboard as Founder console.

---

## 4. Component-by-component reuse matrix

| Upstream component | Path | Responsibility | Local equivalent / gap | Class | Integration boundary | Avoid building | Authority / security | Why not wholesale |
|---|---|---|---|---|---|---|---|---|
| `dispatch_agent_run` | `agent/dispatch.py` | One durable create/interrupt-resume API | H4 `dispatch.py` + H4b `worker_run.py` + agent-start | **ADAPT_PATTERN** | After PlanResult revalidate + CAS acquire; call agent-start `--attach`; never LangGraph as Goal SoT | Ad-hoc per-site spawn + paste wake | Keep fencing in AllTrue; Open SWE has no GoalContract | Depends on LangGraph Agent Server + Deep Agents stack |
| Deterministic thread IDs | `agent/thread_ids.py`, webhook helpers | Same issue/PR/Slack → same thread | WorkerRun.session_id / worktree path unstable across paste | **ADAPT_PATTERN** | Map `(repo, pr\|task_id)` → WorkerRun / session_id | Supervisor memory of “who owns PR” | IDs must bind to lease holder | Their IDs are LangGraph threads |
| GitHub/Slack/Linear webhooks | `agent/webhooks/`, `agent/github/webhook.py` | Verify, allowlist, build context, dispatch | Manual gh; no harness inbox | **ADAPT_PATTERN** | Ingest only → ExternalEvent → Restate/Hatchet signal → harness wake | Custom inbox from scratch | Fail-closed allowlists; App install scope | Full product webhook surface is oversized |
| `/baby-sit` CI watch | `agent/baby_sit.py`, `agent/github/ci.py` | Watch PR CI; wake originating thread | H5 MISSING; EI_ACTIONABLE_CI_* | **ADAPT_PATTERN** | Watch table keyed by WorkerRun/attempt; wake via attach under fence | Manual CI paste loops | Dedup keys; settle window; max retries | Runs inside LangGraph store/crons |
| Completion webhook | `dispatch.py` COMPLETION_WEBHOOK_URL | Run end signal even if agent dies | WorkerRun handoff observe PARTIAL | **ADAPT_PATTERN** | agent-finish / WorkerResult webhook → harness | Silent dead workers | Secret + no loopback | Requires reachable HTTPS endpoint |
| `reconcile_stale_runs` | `agent/reconcile.py` | Cancel stale pending; free busy threads | H7/H8 PARTIAL; hygiene Phase1 | **ADAPT_PATTERN** | Tick cancels stale DispatchAttempt/WorkerRun by age+fence | Manual process kill | Must respect fencing_token | Their “busy thread” ≠ our lease |
| Scheduler graph | `agent/scheduler.py` | Cron fan-out | Disabled portfolio graph-scheduler; no harness tick | **ADAPT_PATTERN** | One local systemd/Restate tick calling harness reconcile+wake drain | Dual schedulers | Do not enable Open SWE scheduler | LangGraph-native |
| Read-only reviewer graph | `agent/reviewer.py`, `graphs/reviewer` | PR review without write tools | CubeLV challenge + GH checks | **ADAPT_PATTERN** | Separate WorkerInvocation mode=review_readonly | Mixing review into implement worker | Never grant write tools to reviewer | Productized differently |
| Per-thread sandbox lifecycle | `agent/sandboxes/`, server.py | Persistent sandbox per thread; fail if unreachable | agent-start worktree | **REFERENCE_ONLY** | Keep agent-start; optionally mirror “fail closed if worktree gone” | Silent worktree recreate | Unreachable ≠ recreate (data loss) | LangSmith/Modal/… providers |
| Deep Agents tool stack | deepagents dep | Files/shell/subagents | Codex/Cursor tools | **REJECT** as CP | Workers remain replaceable CLIs | — | Would relocate authority into LangChain stack | Conflicts with provider-neutral Goal |
| Dashboard / Slack/Linear product | `ui/`, slack, linear | Full factory UX | Not required for H4B | **REJECT** | — | — | New attack surface | Scope explosion |
| Alembic/SQLAlchemy DB | `agent/database/` | Product DB | harness.sqlite + graph-control | **REJECT** | — | Third DB | Violates “no new DB” | — |
| Analyzer review-style learning | `agent/analyzer.py` | Learn review prefs | None | **REFERENCE_ONLY** | Later EI1 | — | Untrusted GH text | Not on autonomy critical path |

**License/runtime (Open SWE):** MIT (LangChain, Inc.). Runtime implies **Python ≥3.14**, LangGraph Agent Server / LangSmith (default sandbox+tracing), optional Modal/Daytona/E2B/Runloop, FastAPI, Slack SDK, Postgres/asyncpg in deps — **heavy**. Production self-host notes LangGraph Agent Server license key. **Do not pull this stack for H4B.**

---

## 5. MetaGPT / OpenHands / other useful patterns

| System | Useful pattern | Class vs our stack |
|---|---|---|
| **OpenHands** Agent Server + Automation + ACP | Multi-CLI ACP; webhook/cron → conversation; not GoalContract | **ADAPT_PATTERN** for provider transport later; **REJECT** as governance SoT (aligned with prior OSS spike) |
| **OpenHands automation** | Schedule/webhook dispatch separate from agent brains | **ADAPT_PATTERN** — same split we want (Restate/Hatchet wake vs harness semantics) |
| **MetaGPT** | Role-cast multi-agent “software company” | **REFERENCE_ONLY** — role metaphor; not durable wake/fencing/exact-SHA |
| **Restate** (prior gate) | Durable webhooks, awakeables, crash recovery | **ADAPT** (already decided) for H5/H7 spine under AllTrue fence |
| **Hatchet** | Slots, concurrency keys, durable waits | **REFERENCE_ONLY** alternative if Restate blocked; not dual-adopt |
| **Temporal** | Workflows | **REJECT** for now (explicit non-scope historically; Restate already chosen for wake) |

---

## 6. What we should NOT copy

- LangGraph/LangSmith as canonical Goal/Run authority  
- Replacing `agent-start` worktrees with cloud sandboxes as SoT  
- Open SWE dashboard as Founder console  
- Their full Slack/Linear surface before H4b/H5 work  
- Deep Agents as mandatory coding runtime (locks provider story)  
- A third durable DB (Alembic/Postgres) beside harness + graph-control  
- Enabling any second scheduler alongside a future harness tick  
- Treating “thread” as substitute for GoalContract + fencing_token  

---

## 7. Whether H4B design should change

**No redesign.** H4B remains: checkout integrity preflight + e2e Plan→Dispatch→WorkerRun→attach→handoff acceptance.

**Optional micro-adapts (documentation/acceptance only, not new framework):**
- Require durable binding keys: `task_id`, `attempt_id`, `session_id`, `worktree`, `fencing_token` recorded before spawn (Open SWE “deterministic id” lesson).
- Fail closed if worktree/session missing (sandbox “unreachable ≠ recreate”).
- Prefer `agent-finish` / WorkerResult as completion signal analog.

Open SWE does **not** remove the need for this Goal; it does not implement our CAS/PlanResult world-bind.

---

## 8. Whether H5 design should change

**Yes — pattern-level only; spine decision unchanged.**

Keep **ADAPT_RESTATE** (or equivalent durable webhook) as ExternalEvent journal. Shape the AllTrue adapter after Open SWE babysit:

1. Opt-in watch keyed by WorkerRun / PR / head_sha  
2. GitHub `check_run` / `check_suite` / Actions conclusion → evaluate  
3. Cron fallback without model call if unchanged  
4. Dedupe delivery/dispatch keys; settle window; max retries  
5. Wake = revalidate PlanResult + fence + `agent-start --attach` (not LangGraph `runs.create`)

**Do not** implement H5 in the deferred H4B Goal. **Do not** unfreeze `restate_gate1` here.

---

## 9. Whether H7 design should change

**Yes — pattern-level only.**

Copy the **thin tick** idea (`scheduler.py` fans tasks; `reconcile_stale_runs` safety net), implemented as **one** harness-owned unit/Restate invocation:

- reconcile leases / stale DispatchAttempt / WorkerRun  
- drain wake queue  
- **Do not** enable portfolio `graph-scheduler` or Open SWE scheduler against AllTrue Goals  

---

## 10. Smallest recommended architecture after reuse

```
FounderIntent / GoalContract     (KEEP AllTrue)
        │
        ▼
PlanResult → DispatchAttempt → WorkerRun + CAS fence   (KEEP)
        │
        ▼
agent-start --attach  (KEEP)   ←── completion/WorkerResult signal (ADAPT from Open SWE)
        │
        ▼
GitHub evidence (PR/CI)

H5 path (later):
  GH CI webhook ──► Restate durable ingest ──► babysit-style evaluate
                         │
                         └──► wake owning WorkerRun under fence

H7 path (later):
  single tick: harness reconcile + wake drain + stale cancel
  (Open SWE scheduler shape; AllTrue authority)
```

**Delete/avoid building:** custom CI paste relay; second scheduler; Open SWE install; LangGraph Goal store; MetaGPT role framework.

---

## 11. Exact upstream sources / commits inspected

| Source | Ref / path |
|---|---|
| `langchain-ai/open-swe` | commit `b73659fb0a2cbe77892348f37910fd607eea2f44` |
| README.md, AGENTS.md, LICENSE, langgraph.json, pyproject.toml | tip |
| `agent/dispatch.py` | durable dispatch contract |
| `agent/baby_sit.py` | CI watch / wake |
| `agent/scheduler.py` | cron fan-out |
| `agent/reconcile.py` | stale pending cancel |
| `agent/github/webhook.py`, `agent/github/ci.py` | CI webhook + check runs |
| `agent/webhooks/common.py` | allowlists / thread metadata |
| `agent/reviewer.py` | read-only reviewer |
| OpenHands README (main, raw) | ACP + automation split |
| MetaGPT README (main, raw) | multi-agent company metaphor |
| Local | `OSS_CONTROL_PLANE_ADOPT_OR_BUILD_SPIKE.md`, durability gate `ADAPT_RESTATE`, harness v4 live meta |

---

## 12. Licensing / runtime dependency findings

| Item | Finding |
|---|---|
| Open SWE license | **MIT** (Copyright LangChain, Inc.) |
| Python | Requires **≥3.14** (langgraph.json / pyproject) — may not match Ubuntu host Python |
| Hard deps | deepagents, langgraph, langgraph-sdk, fastapi, langsmith, slack-sdk, sqlalchemy/asyncpg, multiple sandbox providers |
| Hosted coupling | LangSmith default sandbox/tracing; Agent Server license called out for production self-host |
| Security | Loopback webhooks denied by default (platform); App allowlists — good patterns to mirror, not import blindly |
| Local clone | Evidence-only under `state/alltrue/spikes/…` — **not** installed as service |

---

## 13. Recommended next Goal

**When Codex capacity returns:** execute deferred  
`H4B_E2E_AUTONOMY_ACCEPTANCE`  
(`/home/jerry/workspace/state/alltrue/goals/harness/H4B-E2E/GOAL.json`).

**After H4B accepts:**  
`EXTERNAL_EVENT_WAKE_ADAPTER_V1` using **ADAPT_RESTATE + Open SWE babysit patterns** (not Open SWE install).

**Do not begin** either Goal in this research/persistence task.

---

## 14. Files changed (this task)

See final report §14–15.

---

## 15. Git status

See final report §15 (portfolio-ops discovery worktree may gain a copy of this spike; AllTrue runtime state under `/home/jerry/workspace/state/alltrue/` is host ops state, not necessarily a product git commit).
