# Founder Decisions — Execution Log 2026-07-27

Parent: portfolio-ops #11

## 1. Security read permissions — APPROVED by Founder; **pending App UI + installation re-approval**

Required App UI settings (Founder / App owner action — Operator cannot self-grant):

| UI name | Access |
|---|---|
| Code scanning alerts | Read-only |
| Secret scanning alerts | Read-only |
| Dependabot alerts | Read-only |

**Evidence (2026-07-27T04:30Z mint):** installation token permissions still lack `security_events` / `secret_scanning_alerts` / `vulnerability_alerts`.

After Save changes, **approve the new permissions on the installation** or probes remain 403.

No Administration write. No alert dismiss/write.

## 2. delete_branch_on_merge — APPROVED; **blocked without administration:write**

| Action | Result |
|---|---|
| PATCH repo `delete_branch_on_merge=true` (portfolio-ops, korea-trip-plan) | **403** — `X-Accepted-GitHub-Permissions: administration=write` |
| Delete HIGH-confidence merged branches via Contents/Git refs API | **Done** (see below) |

### Decision request (settings toggle)

Founder must enable in GitHub UI (no App admin write per prior decision):

Repo Settings → General → Pull Requests → **Automatically delete head branches**

- `jerry200176-png/portfolio-ops`
- `jerry200176-png/korea-trip-plan`

### Branches deleted (HIGH only)

**portfolio-ops (8):**  
`chore/claude-instructions-architecture-audit`, `chore/portfolio-maintenance-os`, `chore/sunrise-vercel-forensics`, `chore/1387-1401-mission-checkpoint`, `chore/1387-containment-round2-and-reorder`, `chore/1387-provenance-finding`, `docs/dashboard-instructions-audit-note`, `docs/starred-repos-benchmark-library`

**korea-trip-plan (9):**  
`cursor/couple-preview-media-9dde`, `cursor/impeccable-polish-8383`, `cursor/korea-handbook-foundation-f5a1`, `cursor/lodging-area-scoring-f5a1`, `cursor/open-source-reference-audit-f5a1`, `cursor/pages-deploy-fix-9dde`, `cursor/taste-skill-redesign-8383`, `cursor/ui-ux-pro-max-8383`, `cursor/warm-editorial-design-f49d`

AllTrue orphan branches: **not deleted** — matrix published.

## 3–4. student-evaluation / income-statement-app-releases

See companion docs in this PR / follow-up PRs.

## 5. Workflow retirement — AUDIT_ONLY

Matrix: `ALLTRUE_WORKFLOW_RETIREMENT_MATRIX.md`. No disables executed.

## 6. SHA pinning Phase A

Follow-up PR(s) on AllTrue / Sunrise (staged). Enforcement (`sha_pinning_required`) deferred.

## 7. Merges completed (no admin bypass)

| PR | Merge commit |
|---|---|
| AllTrue #1458 | `d4cb8b0155d7fb8ba4a3a62ac43fc17a229a717c` |
| Sunrise #260 | `b86235795904dd0cb5231da993d3048ce453aa9c` |
| portfolio-ops #10 | `c79478a7feb7b283376f9cf8bea344295dee3395` |
| portfolio-ops #12 | `0d724bc6ae9ab02d9208a4d1846372a44872ca00` |

## 8. Portable hooks + Cursor API

| Item | Status |
|---|---|
| Portable hooks PR | portfolio-ops #14 |
| `CURSOR_ORCHESTRATOR_API_KEY` in this Cloud Agent env | **NOT SET** — Graph activation blocked |
| `/v0/me` verification | **NOT RUN** (no key) |

Credential exposure: **NO**
