# CURRENT_CONTROL_LOOP — Actual workflow (not intended)

**Audit:** `AGENT_COMPANY_CONTROL_PLANE_AUDIT_V1` · 2026-09-17  
Reconstructed from runtime evidence. Stages that do not exist are marked **ABSENT**.

Suggested comparison lifecycle (for gap analysis only):

`INTAKE → RECONCILE → TRIAGE → PLAN → REVIEW → DISPATCH → EXECUTE → VERIFY → INTEGRATE → DEPLOY → RUNTIME_VERIFY → ACCEPT → NOTIFY → FINALIZE → GC → LEARN`

---

## Actual end-to-end graph (today)

```
[Founder prompt / In-App product / GH Issue / CI failure / Ops incident]
        │
        ▼
   INTAKE (human+LLM) ─── ABSENT canonical WorkItem store
        │  persists as: chat + FOUNDER_INBOX.json + DISPATCH_*.json + goals/*/GOAL.json
        ▼
   RECONCILE (Supervisor LLM + gh/curl) ─── PARTIAL; ad-hoc; not harness-owned tick
        │  persists as: CURRENT_STATE.json / CONTROL_PLANE_CANONICAL_STATE.json
        ▼
   TRIAGE (Supervisor LLM) ─── lanes A/B/C WIP limits by convention
        ▼
   PLAN (Worker LLM or Supervisor) ─── harness planner CODE MERGED; often unused in live path
        ▼
   REVIEW (Founder or Supervisor) ─── FOUNDER_INBOX plan-review items
        ▼
   DISPATCH (Supervisor writes DISPATCH_*.json + agent-start)
        │  harness dispatch CLI MERGED but live DB cannot hold DispatchAttempt/WorkerRun
        ▼
   EXECUTE (Codex/Claude/Cursor/cubelv in task worktree)
        │  session manifest in agent-control/sessions
        ▼
   VERIFY (CI via GitHub Actions) ─── strong; deterministic
        │  wake on failure: MANUAL (EI_ACTIONABLE_CI_WORKER_NOT_AUTO_WOKEN)
        ▼
   INTEGRATE (agent squash-merge R0–R3 per fleet policy; Founder for T3/prod)
        ▼
   DEPLOY (Founder Environment approval → deploy.yml → Pi)
        ▼
   RUNTIME_VERIFY (read-only version.json/health; wait-github-deploy)
        ▼
   ACCEPT (Founder / Supervisor artifacts) ─── MERGED ≠ ACCEPTED practiced
        ▼
   NOTIFY ─── ABSENT productized; chat/email ad-hoc
        ▼
   FINALIZE / GC ─── PARTIAL (agent-finish; hygiene scripts; manual)
        ▼
   LEARN ─── ABSENT (EI research ≠ closed feedback loop)
```

Staging (Daan) is a **parallel Founder-interactive** loop, not wired into harness transitions.

---

## Transition questionnaire (per stage)

Legend: D=deterministic, L=LLM, H=human/Founder. Survive: P=process, S=Supervisor session, M=machine.

### INTAKE

| Question | Answer |
|----------|--------|
| Who initiates? | Founder prompt, Supervisor scan of GH/In-App, incident discovery |
| Where persisted? | Chat history; `FOUNDER_INBOX.json`; ad-hoc goal JSON; GH Issues (product SoT for issues only) |
| Authority | None canonical — Supervisor improvises |
| D/L/H | Mostly L+H |
| Survive P/S/M? | Chat: no. JSON: yes if files on disk. GH Issues: yes |
| Dup-safe? | No — duplicates common across JSON + Issues |
| Reconcile / retry / compensate? | No automated intake reconcile |
| Completion evidence | None standardized |
| Founder relay? | **Yes** — often Founder pastes In-App/ops context |

### RECONCILE

| Question | Answer |
|----------|--------|
| Who initiates? | Supervisor at cycle start (Cursor) |
| Persisted? | `CURRENT_STATE.json`, `CONTROL_PLANE_CANONICAL_STATE.json`, `SUPERVISOR_RECONCILE_*.json` |
| Authority | Hand-written; competing with harness.sqlite meta |
| D/L/H | L + some D (`gh`, curl tip) |
| Survive P/S/M? | Files yes; continuous loop no (session-bound) |
| Dup-safe? | Overwrites; no event log |
| Reconcile of reconcile? | Manual |
| Evidence | SHA tips, PR lists, health JSON |
| Founder relay? | Sometimes asks Founder to confirm opaque remote state (esp. Daan Docker) |

### TRIAGE / PLAN / REVIEW

| Stage | Initiator | Persist | Authority | D/L | Survive | Dup-safe | Retry | Founder relay |
|-------|-----------|---------|-----------|-----|---------|----------|-------|---------------|
| TRIAGE | Supervisor | CURRENT_STATE workers[] | Convention WIP A/B/C | L | Session+JSON | Weak | No | Priority disputes |
| PLAN | Worker/Supervisor | PR docs / PlanResult (code) / DISPATCH | Founder for product architecture plans | L (+ harness D unused) | PR yes | Weak | Manual | Plan reviews (#299, H3 historical) |
| REVIEW | Founder/Supervisor | FOUNDER_INBOX | Founder for T3/product | H | JSON yes | Dedupe keys PARTIAL | N/A | **Core Founder role** |

### DISPATCH → EXECUTE

| Question | Answer |
|----------|--------|
| Who initiates? | Supervisor writes DISPATCH_*.json; runs `agent-start` |
| Persisted? | DISPATCH JSON + session manifest; **not** live WorkerRun rows |
| Authority | Supervisor session; fencing exists in code, rarely live-bound |
| D/L | Spawn path D; choice of work L |
| Survive P? | Worktree+branch yes |
| Survive Supervisor restart? | **Partial** — worktree survives; ownership memory often in chat |
| Survive machine restart? | Worktree yes; running CLI no |
| Dup-safe? | agent-start may create duplicate sessions if IDs collide; harness CAS not live |
| Timeout/retry | Manual / Cursor |
| Compensation | Manual supersede PR / abandon worktree |
| Evidence | session_id, branch, PR number |
| Founder relay? | Wake/reattach often relayed |

### VERIFY (CI)

| Question | Answer |
|----------|--------|
| Who initiates? | GitHub on push/PR |
| Persisted? | Actions run history |
| Authority | Required checks + rulesets |
| D/L | Deterministic |
| Survive | Yes (GitHub) |
| Dup-safe | Check runs idempotent enough |
| Reconcile | Manual `gh` / Supervisor |
| Timeout/retry | Actions retries; agent re-push |
| Evidence | Check conclusions |
| Founder relay? | **Often** — “PR X failed” paste; auto-wake ABSENT |

### INTEGRATE → DEPLOY → RUNTIME_VERIFY → ACCEPT

| Stage | Initiator | Persist | Authority | D/L | Survive | Founder relay |
|-------|-----------|---------|-----------|-----|---------|---------------|
| INTEGRATE | Agent (R0–R3) or Founder (T3) | GitHub merge | Fleet merge policy + rulesets | D+H | Yes | T3 / RFID / auth plans |
| DEPLOY | Founder Environment approval | Actions + Pi files | production-activation | D after GO | Yes | **Always for prod** (correct) |
| RUNTIME_VERIFY | wait-github-deploy / curl | deployment.json | Read-only | D | Yes | Rare if waiter used |
| ACCEPT | Founder/Supervisor artifact | ACCEPTED JSON / inbox close | Human | H | Yes | Yes for product flags |

### FINALIZE / GC / LEARN

| Stage | Status | Notes |
|-------|--------|-------|
| FINALIZE | PARTIAL | Delivery closure queue; often waits staging evidence (#296) |
| GC | PARTIAL | `agent-finish` requires explicit approve; hygiene Phase1 scripts ad-hoc |
| LEARN | ABSENT | No planner feedback from failure signatures; EI is offline research |

### Staging (Daan) side loop

Founder-interactive Docker validate-cycle. Agents read-only under `NO_NEW_MUTATION` when incident open. **Not** a harness transition. Migrate failure 2026-09-17 = `AUTHORIZED_MUTATION_EXITED_FAILED` — Founder remediation required.

---

## Durability summary

| Concern | Today |
|---------|-------|
| Work survives CLI crash | Often (worktree + branch) |
| Work survives Supervisor restart | **Weak** — reattach needs human memory or JSON archaeology |
| Work survives machine restart | Worktree yes; in-flight agent no |
| Durable task identity | Designed (WorkerRun) / **not live** |
| Append-only event history | agent_graph dogfood only; AllTrue live = JSON overwrite |
| Continuous reconcile daemon | **No** (graph-scheduler disabled; harness has no forever-loop) |

---

## Deterministic vs LLM (current practice)

| Should be deterministic | Actual |
|-------------------------|--------|
| CI status ingest | Manual/LLM notice |
| Lease reclaim | Code exists; little live use |
| Branch/worktree ownership map | Supervisor memory + JSON |
| Exact-SHA deploy verify | Deterministic when waiter used |
| Dedup intake | Mostly absent |

| Appropriately LLM | Actual |
|-------------------|--------|
| Classify ambiguous product feedback | Ad-hoc |
| Plan / code / review / diagnose | Workers |
| Prioritize under WIP | Supervisor prompts |

**Graph overengineering check:** portfolio-ops built a full event-sourced Run graph + dogfood, then left the scheduler disabled. AllTrue built harness SM + contracts, then left live DB at v1 and ran the company on JSON. Both are **partial platforms**; the live loop is still chat-orchestrated.
