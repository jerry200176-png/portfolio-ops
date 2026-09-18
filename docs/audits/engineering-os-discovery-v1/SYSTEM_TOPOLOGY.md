# SYSTEM_TOPOLOGY

**Audit:** ENGINEERING_OS_DISCOVERY_V1 · 2026-09-18  
**Evidence classes:** FILE / GIT / SQLITE / PROCESS / SYSTEMD / CRON / HTTP_DOC

---

## 1. Executive topology (as-is)

```
Founder / ChatGPT / Cursor chat
        │  (intent, paste wakes, Environment approvals)
        ▼
┌──────────────────────────────────────────────────────────────┐
│  COMPETING “control” surfaces (not one Engineering OS)       │
│                                                              │
│  A. AllTrue AEH                                              │
│     scripts/harness/*  →  state/alltrue/harness.sqlite v4    │
│     GoalContract / Plan / DispatchAttempt / WorkerRun / CAS  │
│                                                              │
│  B. Portfolio graph-control                                  │
│     agent_graph/*  →  state/portfolio-ops/graph-control*.sqlite│
│     Goal / Run / Attempt / Effect / Approval / CanonicalEvent│
│     graph-scheduler.service = DISABLED                       │
│                                                              │
│  C. Session gateway (shared)                                 │
│     agent-control / agent-start → tasks/<project>/<task-id>  │
│                                                              │
│  D. Stale / hollow pointers                                  │
│     ~/workspace/portfolio-ops (exo hollow; scripts missing)   │
│     ~/workspace/AllTrue_System-clean (far behind; no harness) │
└──────────────────────────────────────────────────────────────┘
        │
        ▼
Codex | Cursor | Claude  (replaceable workers — NOT authorities)
        │
        ▼
GitHub (source, PR, CI, evidence) ──► deploy.yml / Vercel
        │
        ▼
Production observe (deployment.json, health, Phase-C, Sunrise outcomes)
        │
        ▼
Outcome learning: Sunrise PARTIAL · AllTrue / EI MOSTLY MISSING
```

**Target architecture (required model — not yet live as one plane):**

```
FounderIntent / GoalContract
  → canonical control plane (reuse AllTrue contracts + Restate adapt for wake)
  → provider-neutral PlanGraph / WorkerInvocation
  → Codex | Cursor | other workers
  → evidence / PR / CI / deployment
  → runtime observation
  → outcome learning
```

CubeLV = replaceable client/challenge surface. GitHub = collaboration + evidence substrate, not orchestration SoT.

---

## 2. Repositories / worktrees / ownership

| Asset | Path | Ownership role | Evidence |
|---|---|---|---|
| AllTrue bare | `/home/jerry/workspace/repos/AllTrue_System.git` | **Canonical product source** | GIT: `main` has `scripts/harness/` |
| Portfolio-ops bare | `/home/jerry/workspace/repos/portfolio-ops.git` | **Fleet control-plane source** | GIT: tip includes agent_graph + audits |
| Sunrise bare | `/home/jerry/workspace/repos/sunrise-cafe.git` | Product source | FILE layout |
| Agent gateway | `/home/jerry/workspace/agent-control` | Session/worktree launcher | FILE + `~/.local/bin/agent-start` symlink |
| EI | `/home/jerry/workspace/engineering-intelligence` | Research pipeline (schedules off) | FILE + GH workflows gated |
| Task worktrees | `/home/jerry/workspace/tasks/{alltrue,portfolio-ops,sunrise,engineering-intelligence}/` | Isolated delivery | agent-start contract |
| AllTrue runtime state | `/home/jerry/workspace/state/alltrue/` | **Harness authority + ops JSON** | SQLITE + JSON |
| Portfolio runtime state | `/home/jerry/workspace/state/portfolio-ops/` | Graph DB + dogfood | SQLITE + PID/cron |
| Hollow “canonical” checkout | `/home/jerry/workspace/portfolio-ops` | **Broken pointer** | NO `AGENT_BOOTSTRAP.md`; `scripts/`/`agent_graph/` only `__pycache__` |
| Forbidden / do-not-edit | `/home/jerry/alltrue`, `AllTrue_System`, `AllTrue_System-clean`, `sunrise-cafe` shared checkouts | Legacy | AGENTS.md / AGENT_BOOTSTRAP |

**Pointer bug:** `agent-start` defaults `COMPANY_CONTROL_PLANE_ROOT` → hollow `/home/jerry/workspace/portfolio-ops`. Tip contracts exist only on task worktrees / bare-derived checkouts.

---

## 3. Durable state machines (two planes)

### 3.1 AllTrue harness (`harness.sqlite`)

**Path:** `/home/jerry/workspace/state/alltrue/harness.sqlite`  
**Meta (2026-09-18):** `schema_version=4`, `authority_role=domain_authority`, `cutover_operationally_accepted=true`, `machine_reboot=UNPROVEN`, `restate_gate1=FROZEN`

| Table | Live rows | Role |
|---|---:|---|
| programs | 5 | Program registry |
| tasks | 7 | Task SM |
| leases | 9 | CAS + fencing |
| worker_runs | 1 | H4b (`handed_off` dogfood) |
| dispatch_attempts | 1 | Persist-before-spawn |
| goals / decision_receipts / checkpoints | 0 | Empty in live DB |
| escalations | 0 | — |
| transitions | 4 | Audit trail |

**Code (MERGED on AllTrue `main`):** `scripts/harness/{contracts,planner,dispatch,worker_run,launcher,leases,store,reconcile,cli,schema_migrate,project_state}.py`  
**Projection:** `CURRENT_STATE.json` (`not_authoritative: true`, `authority: harness.sqlite`)

### 3.2 Portfolio graph-control

**Declared canonical:** `/home/jerry/workspace/state/portfolio-ops/graph-control.sqlite`  
**Live:** 1 goal, 1 run (`waiting_worker`), 1 failed attempt, 0 effects/approvals  
**Richer dogfood DBs:** `graph-control-sched-dogfood.sqlite` (10 goals / 67 attempts) — proof, not fleet SoT

**Code host:** `/home/jerry/workspace/tasks/portfolio-ops/scheduler-runtime/agent_graph/` (and tip worktrees) — models include `CanonicalEvent`, `WorkerResult`, effect journal, RealCodex + external CLI adapters.

**Scheduler:** `graph-scheduler.service` **disabled / inactive**. No live `schedule-run` process.

---

## 4. Control / data flows (actual)

### 4.1 Engineering delivery (AllTrue-dominant today)

1. Founder / Supervisor invents or copies Goal text into chat or `DISPATCH_*.json` / FOUNDER_INBOX.
2. Optional: `python3 -m scripts.harness plan|dispatch` (often Supervisor-driven, not systemd).
3. `agent-start alltrue <task>` creates worktree + manifest; H4b `launcher.py` can `--attach`.
4. Worker opens PR → GitHub Actions CI.
5. On CI failure: **manual wake** (`_wake_*.log`, `DISPATCH_WAKE_*`, AUTONOMY_METRICS `manual_wake_or_task_relaunches: 14`).
6. Agent merges R0–R2 per tip `AUTONOMY_POLICY` (2026-09-04 operator model) when using tip contracts.
7. Production: Founder Environment `production-activation` + exact-SHA `deploy.yml`.
8. Runtime: `deployment.json` / health; Delivery Closure queue is **JSON ops**, not harness table.

### 4.2 Portfolio graph dogfood

1. RealCodex dogfood entered `quota_wait` (resume scheduled 2026-09-19 16:26 +08).
2. Cron `@reboot` + one-shot preresume armed; **all related PIDs dead**; systemd dogfood units disabled.
3. `GRAPH_CONTROL_PLANE_V1_AUTONOMOUS` remains **NO** (no `real-codex-dogfood.done`).

### 4.3 Product feedback

- **AllTrue in-app BugReport** → ops dump → GH issue → Phase-A/C workflows (**product path PRODUCTION_VERIFIED**).
- **Not wired** into `harness.sqlite` Task ingest.
- **Sunrise** Outcome Pipeline + BI cron = strongest outcome-learning skeleton.
- **EI** collect/analyze pipelines CODE/TESTED; GH schedules fail-closed (`EI_AUTOMATION_ENABLED` unset); corpus empty.

---

## 5. Governance / agent config surfaces

| Surface | Location | Authority today |
|---|---|---|
| Fleet bootstrap | tip `governance/AGENT_BOOTSTRAP.md` | Correct on task worktrees; **missing** on hollow checkout |
| Autonomy | tip `AUTONOMY_POLICY.md` (Agent operator) vs hollow 2026-07-25 revoke | **CONFLICTING generations** |
| Capability registry | tip/hollow both stale vs graph+harness | STALE |
| Cursor rules | `~/.cursor/rules`, workspace AGENTS.md | Pointers; not runtime SoT |
| Codex routing | `~/.codex/model-routing.toml` | Session model routing only |
| MCP | Codex Cloudflare MCP; Cursor Context7/Gmail plugins | Untrusted I/O, not orchestration |
| Exo | `.exo/` on worktrees | Experiment locks; not fleet authority |
| ACP | Evaluated in OSS spike | **Not implemented** as control path |

---

## 6. Background automation (runtime)

| Mechanism | State | Evidence |
|---|---|---|
| `graph-scheduler.service` | disabled/inactive | systemctl |
| `graph-realcodex-dogfood-*.service` | disabled | systemctl |
| `portfolio-ops-governance-autopilot.timer` | active waiting; last service **failed** (exit 127) | missing script on hollow checkout |
| Cron dogfood reboot/preresume | armed; PIDs dead | crontab + pidfiles |
| Harness durable tick | **none** | no systemd unit for `scripts.harness` |
| EI scheduled collect | not enabled | workflow `vars.EI_AUTOMATION_ENABLED` |

---

## 7. What this is *not*

- Not a single company Goal authority.
- Not CubeLV-orchestrated.
- Not Codex/Cursor-owned state.
- Not “implemented because documented” — hollow docs and prior audit v1-schema claim are counterexamples.
