# MULTI_MACHINE_RUNTIME

**Audit:** `AGENT_COMPANY_CONTROL_PLANE_AUDIT_V1` · 2026-09-17  
Read-only. No SSH into production; no Docker mutation on Daan.

---

## Naming trap (ops-critical)

| Name | Reality |
|------|---------|
| `daan.lifenet.com.tw` | **Pi production** public tip |
| `pi.lifenet.com.tw` | Pi SSH hostname (documented) |
| `alltrue.daan.lifenet.com.tw` | **Daan server** (staging + Dify) |
| `CubeLV` / `cubelv` | **Coding agent**, not a compute host |

---

## Fleet profiles

### Jerry WSL (implicit control node)

| Field | Evidence |
|-------|----------|
| Role | Supervisor + coding workers + local Restate PoC + self-hosted GH Actions runner |
| Runtime | Linux WSL2; Python harness; agent-control; **no Docker CLI** observed |
| Persistence | `workspace/state`, task worktrees, bare repos, sessions |
| Credentials | No `PI_*` deploy secrets by design; Daan key `~/.ssh/alltrue_daan_stage` |
| Authority | Code/PR/reconcile; not production mutate |
| Availability | Primary operator machine |

### Pi — production

| Field | Evidence |
|-------|----------|
| Role | Production AllTrue (PHP 8.2-FPM + Laravel + local MySQL) |
| Reachable | HTTPS health/version/deployment — tip `16e38fb…` at audit |
| Capacity | SBC; thermal/RAM constrained (exact UNKNOWN without SSH) |
| Worker capability | **Not** a coding worker; backup/monitor cron; Hermes exception only if approved |
| Authority | Deploy via GitHub `deploy.yml` + Environment; agents must not SSH |
| Deploy responsibility | GitHub Actions exact-SHA only |

### Daan — staging (+ co-resident AI stack)

| Field | Evidence |
|-------|----------|
| Role | Isolated staging compose + host Dify/Hermes |
| Reachable | SSH passwordless documented; staging `127.0.0.1:18080` via tunnel |
| Capacity | ~3.4 GiB RAM evidence (Phase0); mem preflight ≥900 MiB; swap pressure |
| Persistence | Host checkout + Docker volumes; `restart: "no"` |
| Worker capability | Staging validation lane only; Docker needs interactive sudo today |
| Authority | Founder-interactive while `WAITING_EXTERNAL` / migrate failed |
| State at audit | `AUTHORIZED_MUTATION_EXITED_FAILED` (vendor autoload / migrate) |

### CubeLV — agent identity

| Field | Evidence |
|-------|----------|
| Role | Untrusted writer agent (`company-agent-contract.yaml` lists `cubelv`) |
| Host services | **None evidenced** |
| Scheduler role | **None** — treat as optional PR author |

---

## Conceptual scheduler / resource model (simplest that survives node loss)

**Do not install Kubernetes/Nomad.**

```
WorkItem (harness SoT)
   │
   ▼
Capability router (labels)
   ├─ coding:*     → Jerry WSL workers (Codex/Claude/Cursor/cubelv)
   ├─ ci:build     → GitHub-hosted Actions (default) / WSL self-hosted runner
   ├─ deploy:prod  → GitHub Actions → Pi (Founder Environment gate)
   └─ stage:validate → Daan compose job (Founder docker session until sudo model fixed)
```

Primitives actually needed now:

1. **Worker registration** — process/session identity already in agent-control; bind to WorkerRun.  
2. **Capability labels** — `coding`, `gh-actions`, `staging-docker`, `prod-readonly-probe`.  
3. **Leases + fencing** — already designed in harness; must be live.  
4. **Heartbeat** — WorkerRun / CLI liveness; reclaim stale.  
5. **Queue routing** — single SQLite/Restate inbox; not multi-cluster.

**Node loss survival:**

| Loss | Effect | Recovery |
|------|--------|----------|
| WSL down | Coding stops; prod keeps serving | Restart WSL; resume WorkerRuns from store |
| Pi down | Prod outage | Existing backup/monitor; not agent-scheduled |
| Daan down | Staging unavailable | Product delivery continues; staging backlog |
| CubeLV unavailable | Fewer PR authors | Other workers |

---

## Anti-patterns (evidenced)

- Self-hosted runner on Pi  
- Always-on staging fighting Dify RAM  
- Agent Docker without Founder session (current sudo model)  
- Treating CubeLV as infrastructure  
- Enabling graph-scheduler and harness dispatcher concurrently without one authority
