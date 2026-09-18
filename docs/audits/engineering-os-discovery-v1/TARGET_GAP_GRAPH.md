# TARGET_GAP_GRAPH

**Audit:** ENGINEERING_OS_DISCOVERY_V1 · 2026-09-18  

Smallest dependency graph to reach:

**Founder Goal → autonomous bounded software delivery loop**

(Discovery → Planning → Engineering → Review → Delivery → Runtime Verification → Outcome Learning)

**Constraint:** reuse existing contracts; no new orchestration framework; no new database; do not dual-enable schedulers.

---

## 1. Already sufficient (do NOT rebuild)

```
[KEEP] GoalContract / EvidenceEnvelope / DecisionReceipt / subject_sha
[KEEP] CAS leases + fencing_token
[KEEP] PlanResult world-bind (H3)
[KEEP] DispatchAttempt persist-before-spawn (H4)
[KEEP] WorkerRun + agent-start --attach (H4b code)
[KEEP] autonomy_gate + exact-SHA deploy.yml + Phase-C allowlist
[KEEP] MERGED ≠ ACCEPTED ≠ DEPLOYED ≠ RUNTIME_VERIFIED ladder
[KEEP] agent-control worktree gateway
[KEEP] ADAPT_RESTATE decision (durability gate) — adapt wake spine only
[KEEP] Sunrise OUTCOME_LOG pattern (copy ideas, don’t fork control plane)
```

---

## 2. Minimal gap graph (critical path)

```
G0 CONTROL_PLANE_CHECKOUT_INTEGRITY
        │  (agents must load tip contracts, not hollow tree)
        ▼
G1 H4B_E2E_WAKE_ACCEPTANCE
        │  (prove Plan→Dispatch→attach→handoff without paste)
        ▼
G2 EXTERNAL_EVENT_WAKE_ADAPTER_V1   ◄── ADAPT_RESTATE (already decided)
        │  (CI/webhook → durable wake → WorkerRun under AllTrue fence)
        ▼
G3 SINGLE_DURABLE_RECONCILE_TICK
        │  (one supervised loop owning harness reconcile+wake drain;
        │   do NOT enable graph-scheduler in parallel on AllTrue Goals)
        ▼
G4 CANONICAL_INTAKE_WORKITEM_V1
        │  (BugReport/GH → Task/GoalContract; dedupe)
        ▼
G5 DELIVERY_RUNTIME_OBSERVE_CLOSE
        │  (deployment.json reconcile → close Delivery Closure;
        │   optional TrueFit flag verify — still Founder for activation)
        ▼
   [LATER] OUTCOME_LEARNING_ALLTRUE_V1  (metrics → re-rank; after G4–G5)
   [LATER] FLEET_GOAL_FEDERATION        (map graph Goal↔harness; only if needed)
```

This is **five edges** on the autonomy critical path (G1–G5), plus G0 precondition. Matches `NEXT_5_BOUNDED_GOALS.md` (G0 folded into Goal 1 or treated as first Goal).

---

## 3. Why this order

| Edge | Removes Founder | Depends on |
|---|---|---|
| Checkout integrity | Wrong-policy merges / broken autopilot | none |
| H4b e2e acceptance | Paste start/attach uncertainty | store v4 (done) |
| ExternalEvent wake | Paste CI wakes (metrics: 14/night) | H4b identity stable |
| Durable tick | Session-death stalls | wake adapter or at least queue |
| Intake WorkItem | Founder as ticket clerk | Task SM exists |
| Delivery observe close | Founder as deploy spreadsheet | deploy evidence URLs exist |

**Explicitly deferred (not on minimal path):** AI Company UI, Exo expansion, EI full enablement, OPA/Sigstore, replacing harness with Restate, enabling portfolio graph-scheduler as AllTrue SoT, ACP.

---

## 4. Mapping to target architecture roles

| Target role | Reuse | Gap |
|---|---|---|
| FounderIntent / GoalContract | H2 contracts | Intake from product + Founder Goal text binder |
| Canonical control plane | harness.sqlite domain_authority | Fleet federation undecided; keep AllTrue-local for product delivery |
| PlanGraph / WorkerInvocation | H3 PlanResult + H4 DispatchAttempt | Provider-neutral already in spirit; graph WorkerResult is sibling |
| Replaceable workers | agent-start + Codex/Cursor | OK |
| Evidence / PR / CI | GitHub | Wake missing |
| Runtime observation | deployment.json + health | Auto-close missing |
| Outcome learning | Sunrise pattern | AllTrue missing |

---

## 5. Anti-goals (would increase Founder load or risk)

- New SQLite “company OS” beside the two existing DBs
- Enabling `graph-scheduler` + harness dispatcher without federation contract
- Treating CubeLV/Codex as authorities
- Broad Restate rewrite of GoalContract/leases
- More governance documents without wake/intake wiring
- Declaring EI “live” while `EI_AUTOMATION_ENABLED` is off and corpus empty

---

## 6. Success condition (system-level)

A Founder-supplied GoalContract (with risk tier + success condition) can proceed through bounded product delivery such that:

1. next task selection does not require chat paste,
2. CI failures re-enter the owning WorkerRun without paste,
3. supervisor death does not lose the wake/reconcile queue,
4. production activation remains Founder-gated for high blast radius,
5. runtime evidence closes or escalates Delivery Closure without spreadsheet memory.

Until (1)–(3) hold, “Goal-only” autonomy is **aspirational**.
