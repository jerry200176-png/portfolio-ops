# Portfolio GitHub Audit — 2026-07

> **Auditor:** Jerry GitHub Operator (App installation)  
> **Audit date:** 2026-07-27  
> **Credential exposure:** NO  
> **Method:** Installation API authoritative inventory + REST probes + workflow file parse + Actions run stats  
> **Scope:** All repositories currently installed for Jerry GitHub Operator App

## Phase 0 closeout — AllTrue_System #1451

| Check | Result | Evidence |
|---|---|---|
| State | MERGED | PR closed `merged_at=2026-07-27T03:29:21Z` |
| Head match | `1e2f125beecf02e50fbaf4cc8d9c8e7c4282bf78` | Exact match pre-merge |
| Base | `main` | Confirmed |
| Draft | false | Confirmed |
| Mergeable | CLEAN / mergeable=true | Confirmed |
| Unresolved threads | 0 | GraphQL |
| Required checks | all success | ruleset `main-protection` |
| Presubmit CHECK 0–10 | all success | job `89877251231` |
| CHECK 2 size (authoritative) | **507** lines | CI log `PR size: 507 lines changed` |
| PR body size claim | 513 (stale) | Corrected to 507 from CI log |
| Merge method | `--merge --match-head-commit` (no admin/bypass) | `gh pr merge 1451` |
| Merge commit | `09ea861260b6feca47ebb4bdacea4d5d415d3eb4` | main HEAD |
| Head in main ancestry | YES | main history contains approved head |
| Deploy | success run `30234848351` | workflow_run after CI |
| Deployed SHA | `09ea8612…` | deploy log + `version.json` |
| Health | `{"status":"ok"}` | `https://daan.lifenet.com.tw/api/v1/health` |
| version.json | `{"t":"2026-07-27 11:33","hash":"09ea8612"}` | public |
| Deploy smoke | passed | health/branches/auth/me/class-sessions/learning-records/trust-summary + post-merge |
| StudentsList in bundle | YES | production `index-*.js` contains StudentsList / 學生列表 |
| UI Foundation fixture leak | NO | `lint:ui-fixtures` ✅; bundle scan no `pilot-mount`/`e2e-foundation-token`; fixture URLs return SPA index fallback |

## Executive summary

Installation currently covers **9 repositories** (API authoritative; matches founder-known list). Governance maturity is **highly uneven**: AllTrue and Sunrise carry production risk and heavy Actions spend; several personal/prototype repos have near-zero governance overhead (correct); portfolio-ops is the right control plane but lacks CI and retains merged branches because `delete_branch_on_merge=false`.

Top systemic problems (evidence-backed):
1. **Actions minutes waste** — Sunrise `Autonomous Engineering Loop` 770/1000 sampled runs cancelled (disabled manually but historical burn); AllTrue ~49 workflow definitions with many one-off ops/diagnose workflows still active.
2. **Security alert APIs inaccessible** — App lacks `security_events` / `secret_scanning_alerts` / `vulnerability_alerts` read → cannot verify Dependabot/code scanning alert hygiene from Operator identity.
3. **Supply-chain pinning weak** — majority of workflows pin Actions to floating major tags (`v4`), not commit SHAs; `sha_pinning_required=false` on all probed repos.
4. **Required-check / workflow sprawl on AllTrue** — 9 required checks + many advisory workflows; Presubmit failure rate ~24% in 90d sample creates founder friction.
5. **Branch hygiene debt** — AllTrue 35 branches with many orphan agent branches; portfolio-ops 8 high-confidence merged leftovers; korea-trip many merged cursor branches.
6. **Git protocol gap** — Operator can use Contents/Git Data API on portfolio-ops but `git clone` over HTTPS returns repository not found (Contents API works). Documented as operational friction, not a product outage.

## Installation inventory (authoritative)

| Repository | Visibility | Default | Tier | Last push | Open issues | Open PRs | Workflows |
|---|---|---|---|---|---:|---:|---:|
| `jerry200176-png/AllTrue_System` | public | `main` | Tier 0 | 2026-07-27 | 76 | 11 | 47 |
| `jerry200176-png/alltrue_studyplan` | public | `main` | Tier 3 | 2026-03-05 | 0 | 0 | 1 |
| `jerry200176-png/income-statement-app` | private | `main` | Tier 2 | 2026-05-31 | 0 | 0 | 2 |
| `jerry200176-png/income-statement-app-releases` | public | `main` | Tier 4 | 2026-05-31 | 0 | 0 | 0 |
| `jerry200176-png/korea-trip-plan` | public | `main` | Tier 3 | 2026-07-24 | 1 | 1 | 1 |
| `jerry200176-png/portfolio-ops` | private | `main` | Tier 1 | 2026-07-25 | 0 | 1 | 0 |
| `jerry200176-png/student-evaluation` | public | `main` | Tier 3 | 2026-02-07 | 0 | 0 | 0 |
| `jerry200176-png/sunrise-cafe` | public | `main` | Tier 0 | 2026-07-27 | 4 | 1 | 15 |
| `jerry200176-png/vibe-app-store` | public | `master` | Tier 3 | 2026-04-05 | 0 | 0 | 1 |

## Audit completeness

| Area | Status | Notes |
|---|---|---|
| Repo metadata / settings (readable fields) | Complete | administration=read |
| Branches / default | Complete | |
| Rulesets | Complete | |
| Classic branch protection | Complete | 404 = none (not permission denial when `administration=read` accepted) |
| Actions policy | Complete | |
| Workflows + files | Complete | file contents via Contents API |
| Workflow runs (stats) | Partial | AllTrue & Sunrise capped at 1000 runs/90d API page budget |
| Environments | Complete | |
| Deployments | Complete | |
| Issues / PRs / labels / milestones | Complete | |
| Releases / tags | Complete | |
| README / docs tree | Complete | |
| Code scanning / secret scanning / Dependabot alerts | **Blocked** | 403 — see PERMISSION_GAPS.md |
| Git clone (portfolio-ops) | **Blocked** | API OK; git HTTPS not found — use Git Data API |

## Changes made this engagement

| Change | Result |
|---|---|
| Merge AllTrue #1451 | Done — merge commit `09ea861…`; deploy success |
| Production mutations (beyond #1451 deploy) | 0 |
| Ruleset / protection / secrets / visibility changes | 0 |
| Branch deletions | 0 (candidates only) |
| Mass issue/PR closes | 0 |
| This audit branch + docs PR on portfolio-ops | Created |
| Umbrella Issue | Created (see ISSUE_PR_HYGIENE / final report) |

## Related documents

- [REPOSITORY_SCORECARD.md](./REPOSITORY_SCORECARD.md)
- [WORKFLOW_INVENTORY.md](./WORKFLOW_INVENTORY.md)
- [BRANCH_CLEANUP_CANDIDATES.md](./BRANCH_CLEANUP_CANDIDATES.md)
- [ISSUE_PR_HYGIENE.md](./ISSUE_PR_HYGIENE.md)
- [DOCUMENTATION_MAP.md](./DOCUMENTATION_MAP.md)
- [PERMISSION_GAPS.md](./PERMISSION_GAPS.md)
- [90_DAY_REMEDIATION_PLAN.md](./90_DAY_REMEDIATION_PLAN.md)

