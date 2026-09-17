# CONTROL_PLANE_UI_SPEC — Founder Console (define only)

**Audit:** `AGENT_COMPANY_CONTROL_PLANE_AUDIT_V1` · 2026-09-17  
**DO NOT IMPLEMENT** in this Goal. Aligns with `AI_COMPANY_UI` spike: ADAPT Restate UI + KEEP_CUSTOM boards.

---

## Purpose

Replace repetitive prompts/terminal supervision with a single command surface answering:

| Question | Primary widget |
|----------|----------------|
| What work exists? | Work queue (filter by lane/risk/state) |
| What is running? | Live WorkerRuns |
| Which agent owns it? | worker_id / CLI / cubelv |
| Which machine? | capability node (Jerry/Actions/Daan) — never “CubeLV host” |
| What is blocked? Why? | Blocked reason enum + evidence link |
| What requires Founder? | Decision inbox |
| Which PR/CI/deploy? | Linked delivery strip |
| What failed / retrying? | Failure + retry counters |
| What changed in production? | Prod tip delta since last accept |
| What resources are stale? | GC candidates |
| Budget? | Token/cost strip (P2; may be empty initially) |

---

## Minimum useful MVP (scope ceiling)

**In:**

1. **Decision Inbox** — APPROVE / REJECT / DEFER with DecisionReceipt binding (subject_sha, scope).  
2. **Work Board** — WorkItem cards with state lifecycle chips (not a generic dashboard soup).  
3. **Run Inspector** — one WorkItem → WorkerRun → session → PR → checks → deploy SHA.  
4. **Relay Alerts** — CI failed & not woken; lease expired; reconcile drift.  
5. **Prod Strip** — current `deployment.json` SHA vs main tip (read-only).

**Out of MVP:**

- Full IDE  
- Graph node editor  
- Multi-cluster ops  
- Replacing GitHub PR review UI  
- Auto-approve production

---

## Founder actions (verbs only)

`APPROVE` · `REJECT` · `CHANGE_PRIORITY` · `PAUSE` · `CANCEL` · `RETRY` · `INSPECT`

No free-form “go do the thing” as the primary path. Optional comment field attaches to DecisionReceipt.

---

## Data dependencies (blockers)

Console is useless before:

1. harness.sqlite schema v4+ live authority  
2. WorkerRun rows for active work  
3. Event/projection API (even if local SQLite read + gh poll)

Building UI on `CURRENT_STATE.json` hand edits = fake automation UI.

---

## UX principles (anti-slop)

- One composition for the home view: **Inbox + Running + Blocked**  
- Brand: AllTrue / company ops — not generic “AI Agent Dashboard”  
- Prefer dense operational typography over marketing hero  
- Restate UI may be embedded/linked for invocation traces; custom boards own WorkItem/Founder decisions

---

## Success metric

Founder days without opening a Supervisor chat to relay CI failures or reattach workers — while still using Console for true GO/NO-GO decisions.
