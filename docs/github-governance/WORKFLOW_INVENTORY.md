# Workflow Inventory — 2026-07

Parsed from workflow file contents via Contents API. Secret **values** never read.

Total workflow files parsed (excl. some dynamic): 65

## Portfolio findings (P0–P3)
| Sev | Finding | Evidence | Remediation | ROI | Regression risk |
|---|---|---|---|---|---|
| P0 | Sunrise Autonomous Engineering Loop historical burn | sunrise-cafe `autonomous-loop.yml` disabled_manually but 770 cancelled runs in 90d sample (median ~80s) — largest minutes sink observed. | Disable/delete after Founder approval; ensure no schedule still registered. | High ROI minutes recovery | Low if already disabled |
| P0 | AllTrue required-check + workflow sprawl cost | 49 workflow defs; 1000-run sample dominated by CI/security/presubmit; Presubmit fail rate ~24%. | Consolidate one-off ops workflows; keep diagnose workflows workflow_dispatch-only with path filters. | High founder time + Actions $ | Medium — need careful required-check migration (Founder decision) |
| P1 | Floating Action major tags | Most workflows use `actions/*@v4` etc.; repo Actions `sha_pinning_required=false`. | Pin critical deploy/CI to SHAs or enable pin policy on Tier 0. | Supply-chain risk reduction | Medium — pin updates need Dependabot |
| P1 | Security alert APIs 403 | Cannot read code scanning / secret scanning / Dependabot alerts as Operator. | Grant minimal read permissions (see PERMISSION_GAPS). | Blind spot on vuln/secret posture | None (read-only) |
| P1 | Sunrise Verify Production flake | Verify Production success_rate 0.52 in sample; median 534s. | Keep read-only (already direction of #258); reduce flake; separate from deploy owner. | Deploy confidence | Low |
| P2 | Missing timeout-minutes | Multiple scheduled/monitor workflows lack timeout (backup-restore, dora, pi-health, osv, sunrise ci/hygiene/governance). | Add conservative timeouts. | Prevents runaway minutes | Very low |
| P2 | Missing concurrency on PR workflows | agent-provenance / several CI workflows lack concurrency/cancel-in-progress. | Add cancel-in-progress for PR lanes. | Less duplicate compute | Very low |
| P2 | AllTrue `|| true` / continue-on-error patterns | Present in ci.yml, deploy.yml, many ops workflows — can mask failures. | Audit each; keep only where intentional non-blocking. | False confidence | Medium |
| P3 | student-evaluation / portfolio-ops zero workflows | OK for tier, but portfolio-ops could use docs lint; student-evaluation has node_modules committed. | Optional minimal CI; sanitize node_modules. | Hygiene | Low |

## Inventory by repository
### `jerry200176-png/AllTrue_System`

Run window: **90d** · sampled runs: **1000**

| Workflow | Path | State | Triggers | Timeout | Concurrency | Top perms write | Secrets (names) | 90/180d runs | Success | Fail | Cancel | Median s |
|---|---|---|---|---|---|---|---|---:|---:|---:|---:|---:|
| 1387 DB Password Rotation (Founder-triggered, generates own credential) | `.github/workflows/1387-db-password-rotation.yml` | active | workflow_dispatch | Y | Y | — | PI_HOST,PI_HOST_KEY,PI_SSH_KEY,PI_USER | — | — | — | — | — |
| 1401 Privacy Impact Audit (read-only) | `.github/workflows/1401-impact-audit.yml` | active | workflow_dispatch | Y | Y | — | PI_HOST,PI_HOST_KEY,PI_SSH_KEY,PI_USER | 1 | 1.0 | 0.0 | 0.0 | 13.0 |
| In-app | `.github/workflows/173-lr-merge-repair.yml` | active | workflow_dispatch | Y | Y | — | PI_SSH_HOST,PI_SSH_KEY,PI_SSH_USER | — | — | — | — | — |
| In-app | `.github/workflows/173-supersede-repair.yml` | active | workflow_dispatch | Y | Y | — | PI_SSH_HOST,PI_SSH_KEY,PI_SSH_USER | — | — | — | — | — |
| Agent Session Provenance | `.github/workflows/agent-provenance.yml` | active | pull_request | Y | N | — | — | 67 | 0.881 | 0.119 | 0.0 | 10.0 |
| Backup Restore Verification | `.github/workflows/backup-restore-test.yml` | active | schedule,workflow_dispatch | N | N | — | PI_HOST,PI_HOST_KEY,PI_SSH_KEY,PI_USER | 1 | 1.0 | 0.0 | 0.0 | 14.0 |
| Branch Hygiene Report (daily dry-run) | `.github/workflows/branch-hygiene.yml` | active | push,schedule,workflow_dispatch | Y | N | — | — | 1 | 1.0 | 0.0 | 0.0 | 11.0 |
| Bug detail dump (read-only) | `.github/workflows/bug-detail-dump.yml` | active | push,workflow_dispatch | Y | Y | — | PI_HOST_KEY,PI_SSH_HOST,PI_SSH_KEY,PI_SSH_USER | — | — | — | — | — |
| Bug Phase-C allowlist resolve (Pi) | `.github/workflows/bug-phase-c-allowlist.yml` | active | push,workflow_dispatch | Y | Y | — | PI_HOST_KEY,PI_SSH_HOST,PI_SSH_KEY,PI_SSH_USER | — | — | — | — | — |
| Bug Queue Dump (read-only) | `.github/workflows/bug-queue-dump.yml` | active | push,workflow_dispatch | Y | Y | — | PI_HOST_KEY,PI_SSH_HOST,PI_SSH_KEY,PI_SSH_USER | — | — | — | — | — |
| CI — PHPUnit Tests | `.github/workflows/ci.yml` | active | pull_request,push,workflow_dispatch | Y | Y | — | — | 99 | 0.596 | 0.111 | 0.071 | 180.0 |
| ClassSession Duplicate Diagnose (push) | `.github/workflows/classsession-duplicate-diagnose-push.yml` | active | push,workflow_dispatch | Y | Y | — | PI_SSH_HOST,PI_SSH_KEY,PI_SSH_USER | — | — | — | — | — |
| Security Scan | `.github/workflows/codeql.yml` | active | pull_request,push,schedule | Y | Y | — | — | 93 | 0.602 | 0.129 | 0.032 | 57.0 |
| Control Plane Enforce | `.github/workflows/control-plane-enforce.yml` | active | pull_request,push | Y | Y | — | — | 53 | 0.774 | 0.0 | 0.0 | 12.0 |
| Credential Fingerprint Audit (read-only) | `.github/workflows/credential-fingerprint-audit.yml` | active | workflow_dispatch | Y | Y | — | PI_HOST,PI_HOST_KEY,PI_SSH_KEY,PI_USER | — | — | — | — | — |
| DB Password Fingerprint Audit — issue | `.github/workflows/db-password-fingerprint-audit.yml` | active | workflow_dispatch | Y | Y | — | PI_HOST,PI_HOST_KEY,PI_SSH_KEY,PI_USER | 1 | 0.0 | 1.0 | 0.0 | 13.0 |
| Dependency Review | `.github/workflows/dependency-review.yml` | active | pull_request | Y | Y | — | — | 67 | 0.0 | 0.0 | 0.0 | 1.0 |
| Deploy to Pi | `.github/workflows/deploy.yml` | active | workflow_run | Y | Y | — | GITHUB_TOKEN,PI_SSH_HOST,PI_SSH_KEY,PI_SSH_USER,SENTRY_DSN,SMOKE_BRANCH_ID,SMOKE_TEACHER_LOGIN,SMOKE_TEACHER_PASSWORD | 20 | 0.95 | 0.0 | 0.0 | 35.0 |
| Docs Integrity | `.github/workflows/docs-integrity.yml` | active | pull_request,schedule,workflow_dispatch | Y | Y | — | — | 79 | 0.696 | 0.0 | 0.025 | 16.0 |
| DORA Metrics Weekly Report | `.github/workflows/dora-metrics.yml` | active | schedule,workflow_dispatch | N | N | — | GITHUB_TOKEN | — | — | — | — | — |
| High-Risk Test Gate | `.github/workflows/high-risk-test-gate.yml` | active | pull_request | Y | Y | — | — | 80 | 0.713 | 0.0 | 0.013 | 9.0 |
| .htaccess Guard | `.github/workflows/htaccess-guard.yml` | active | pull_request | Y | Y | — | — | 80 | 0.713 | 0.0 | 0.013 | 10.0 |
| Leave/Makeup Evidence Closeout (Pi) | `.github/workflows/leave-makeup-evidence-closeout.yml` | active | push,workflow_dispatch | Y | Y | — | PI_SSH_HOST,PI_SSH_KEY,PI_SSH_USER | — | — | — | — | — |
| MemPalace Monthly Reminder | `.github/workflows/mempalace-monthly.yml` | active | schedule,workflow_dispatch | N | N | — | GITHUB_TOKEN | — | — | — | — | — |
| Migration Dry-run | `.github/workflows/migration-dryrun.yml` | active | pull_request | Y | Y | — | — | 11 | 1.0 | 0.0 | 0.0 | 47.0 |
| Missing Tests Warning | `.github/workflows/missing-tests-warn.yml` | active | pull_request | Y | Y | pull-requests | — | 79 | 0.709 | 0.0 | 0.013 | 11.0 |
| Open Follow-up Issues (idempotent) | `.github/workflows/open-followup-issues.yml` | active | push,workflow_dispatch | Y | Y | contents,issues,pull-requests | GITHUB_TOKEN | — | — | — | — | — |
| Director leave-HC pack + | `.github/workflows/ops-director-leave-hc-pack.yml` | active | push,workflow_dispatch | Y | Y | issues | GITHUB_TOKEN,PI_SSH_HOST,PI_SSH_KEY,PI_SSH_USER | — | — | — | — | — |
| Leave-cascade slot repair (bundle-gated) | `.github/workflows/ops-leave-cascade-repair.yml` | active | workflow_dispatch | Y | Y | issues | PI_SSH_HOST,PI_SSH_KEY,PI_SSH_USER | — | — | — | — | — |
| Leave-HC campus review tracker (#1342) | `.github/workflows/ops-leave-hc-review-tracker.yml` | active | push,schedule,workflow_dispatch | Y | Y | issues | GITHUB_TOKEN,PI_SSH_HOST,PI_SSH_KEY,PI_SSH_USER | 2 | 1.0 | 0.0 | 0.0 | 27.0 |
| Leave vacated-weeks scan (read-only) | `.github/workflows/ops-leave-vacated-weeks-scan.yml` | active | workflow_dispatch | Y | Y | — | PI_HOST,PI_HOST_KEY,PI_SSH_KEY,PI_USER | — | — | — | — | — |
| Ops Portfolio + TD-059 + Leave CSV (read-only) | `.github/workflows/ops-portfolio-td059-leave-audit.yml` | active | push,workflow_dispatch | Y | Y | issues | GITHUB_TOKEN,PI_SSH_HOST,PI_SSH_KEY,PI_SSH_USER | — | — | — | — | — |
| Stranded | `.github/workflows/ops-stranded-classify-refresh.yml` | active | push,workflow_dispatch | Y | Y | issues | GITHUB_TOKEN,PI_SSH_HOST,PI_SSH_KEY,PI_SSH_USER | — | — | — | — | — |
| TD-059 monitored risk probe (#1343) | `.github/workflows/ops-td059-monitor.yml` | active | push,schedule,workflow_dispatch | Y | Y | issues | GITHUB_TOKEN,PI_SSH_HOST,PI_SSH_KEY,PI_SSH_USER | — | — | — | — | — |
| OSV Supply-chain Deep Scan | `.github/workflows/osv-scanner.yml` | active | schedule,workflow_dispatch | N | N | security-events,security-events | — | — | — | — | — | — |
| Pi Health Monitor | `.github/workflows/pi-health.yml` | active | schedule,workflow_dispatch | N | N | — | PI_HOST,PI_HOST_KEY,PI_SSH_KEY,PI_USER,UPTIMEROBOT_API_KEY | 2 | 1.0 | 0.0 | 0.0 | 95.0 |
| Post audit conclusions to Issues | `.github/workflows/post-audit-issue-comments.yml` | active | push,workflow_dispatch | Y | N | issues | GITHUB_TOKEN | — | — | — | — | — |
| Presubmit Gate | `.github/workflows/presubmit.yml` | active | pull_request | Y | Y | — | — | 79 | 0.468 | 0.241 | 0.013 | 12.0 |
| Release Tag | `.github/workflows/release.yml` | active | push,workflow_dispatch | Y | Y | contents | GITHUB_TOKEN | 10 | 1.0 | 0.0 | 0.0 | 14.0 |
| Rollback Readiness | `.github/workflows/rollback-readiness.yml` | active | pull_request,schedule,workflow_dispatch | Y | Y | — | — | 12 | 1.0 | 0.0 | 0.0 | 12.0 |
| Secret Scan | `.github/workflows/secret-scan.yml` | active | pull_request | Y | Y | — | — | 80 | 0.713 | 0.0 | 0.013 | 12.0 |
| Slow Query Report | `.github/workflows/slow-query-report.yml` | active | schedule,workflow_dispatch | N | N | — | PI_HOST,PI_HOST_KEY,PI_SSH_KEY,PI_USER | — | — | — | — | — |
| Teacher Sign-in Diagnostic (manual) | `.github/workflows/teacher-signin-diagnose.yml` | active | workflow_dispatch | Y | Y | — | PI_SSH_HOST,PI_SSH_KEY,PI_SSH_USER | — | — | — | — | — |
| Teacher Sign-in Recovery (manual) | `.github/workflows/teacher-signin-recovery.yml` | active | workflow_dispatch | Y | Y | — | PI_SSH_HOST,PI_SSH_KEY,PI_SSH_USER | — | — | — | — | — |
| UI Smoke (Playwright) | `.github/workflows/ui-smoke.yml` | active | pull_request,schedule,workflow_dispatch | Y | N | — | SMOKE_BASE_URL,SMOKE_DIRECTOR_PASS,SMOKE_DIRECTOR_USER,SMOKE_TEACHER_PASS,SMOKE_TEACHER_USER | 79 | 0.709 | 0.013 | 0.0 | 11.0 |

### `jerry200176-png/alltrue_studyplan`

Run window: **180d** · sampled runs: **10**

| Workflow | Path | State | Triggers | Timeout | Concurrency | Top perms write | Secrets (names) | 90/180d runs | Success | Fail | Cancel | Median s |
|---|---|---|---|---|---|---|---|---:|---:|---:|---:|---:|
| Deploy to GitHub Pages | `.github/workflows/main.yml` | active | push,workflow_dispatch | N | Y | id-token | — | 10 | 1.0 | 0.0 | 0.0 | 46.0 |

### `jerry200176-png/income-statement-app`

Run window: **90d** · sampled runs: **91**

| Workflow | Path | State | Triggers | Timeout | Concurrency | Top perms write | Secrets (names) | 90/180d runs | Success | Fail | Cancel | Median s |
|---|---|---|---|---|---|---|---|---:|---:|---:|---:|---:|
| CI 自動測試 | `.github/workflows/ci.yml` | active | pull_request,push | N | N | — | — | 62 | 0.984 | 0.016 | 0.0 | 47.0 |
| 自動打包 Release | `.github/workflows/release.yml` | active | push | N | N | contents | CODE_SIGN_PFX_BASE64,CODE_SIGN_PFX_PASSWORD | 26 | 0.962 | 0.038 | 0.0 | 72.0 |

### `jerry200176-png/korea-trip-plan`

Run window: **90d** · sampled runs: **220**

| Workflow | Path | State | Triggers | Timeout | Concurrency | Top perms write | Secrets (names) | 90/180d runs | Success | Fail | Cancel | Median s |
|---|---|---|---|---|---|---|---|---:|---:|---:|---:|---:|
| CI | `.github/workflows/ci.yml` | active | pull_request,push | N | N | id-token | — | 220 | 0.795 | 0.205 | 0.0 | 135.0 |

### `jerry200176-png/sunrise-cafe`

Run window: **90d** · sampled runs: **1000**

| Workflow | Path | State | Triggers | Timeout | Concurrency | Top perms write | Secrets (names) | 90/180d runs | Success | Fail | Cancel | Median s |
|---|---|---|---|---|---|---|---|---:|---:|---:|---:|---:|
| Agent Session Provenance | `.github/workflows/agent-provenance.yml` | active | pull_request | Y | N | — | — | 43 | 0.628 | 0.372 | 0.0 | 8.0 |
| Apply migration market-parity | `.github/workflows/apply-migration-market-parity.yml` | active | push,workflow_dispatch | Y | N | — | NEXT_PUBLIC_SUPABASE_URL,SUPABASE_DB_URL,SUPABASE_SERVICE_ROLE_KEY,VERCEL_TOKEN | — | — | — | — | — |
| Apply migration ops_events | `.github/workflows/apply-migration-ops-events.yml` | active | push,workflow_dispatch | Y | N | — | CRON_SECRET,NEXT_PUBLIC_SUPABASE_URL,SUPABASE_DB_URL,SUPABASE_SERVICE_ROLE_KEY,VERCEL_TOKEN | — | — | — | — | — |
| Apply migration is_reminded_7d | `.github/workflows/apply-migration-reminded-7d.yml` | active | workflow_dispatch | Y | N | — | CRON_SECRET,NEXT_PUBLIC_SUPABASE_URL,SUPABASE_DB_URL,SUPABASE_SERVICE_ROLE_KEY | — | — | — | — | — |
| Autonomous Canary | `.github/workflows/autonomous-canary.yml` | active | push,schedule,workflow_dispatch | Y | Y | contents,pull-requests,actions,issues | GITHUB_TOKEN,OPENAI_API_KEY,VERCEL_TOKEN | — | — | — | — | — |
| Autonomous Engineering Loop | `.github/workflows/autonomous-loop.yml` | disabled_manually | push,schedule,workflow_dispatch,workflow_run | Y | Y | contents,pull-requests,actions,issues | GITHUB_TOKEN,OPENAI_API_KEY,VERCEL_TOKEN | 770 | 0.0 | 0.0 | 1.0 | 80.0 |
| Business Intelligence | `.github/workflows/business-intelligence.yml` | active | schedule,workflow_dispatch | Y | Y | contents | CRON_SECRET,CTO_OUTCOME_SECRET,NEXT_PUBLIC_SUPABASE_URL,SUPABASE_SERVICE_ROLE_KEY | 12 | 1.0 | 0.0 | 0.0 | 48.0 |
| CI | `.github/workflows/ci.yml` | active | pull_request,push | N | N | — | E2E_ADMIN_PASSWORD,GITHUB_TOKEN | 84 | 0.869 | 0.131 | 0.0 | 280.0 |
| GitHub Hygiene | `.github/workflows/github-hygiene.yml` | active | push,schedule,workflow_dispatch | N | Y | issues,pull-requests | GITHUB_TOKEN | 2 | 1.0 | 0.0 | 0.0 | 9.0 |
| Engineering Governance | `.github/workflows/governance.yml` | active | schedule,workflow_dispatch | N | N | — | GITHUB_TOKEN | 1 | 0.0 | 1.0 | 0.0 | 66.0 |
| Orchestrator Heartbeat | `.github/workflows/orchestrator.yml` | active | schedule,workflow_dispatch | N | N | — | GITHUB_TOKEN | 9 | 1.0 | 0.0 | 0.0 | 123.0 |
| Production deploy and migrate | `.github/workflows/production-deploy-migrate.yml` | active | push,workflow_dispatch | Y | Y | — | CRON_SECRET,NEXT_PUBLIC_SUPABASE_URL,SUPABASE_DB_URL,SUPABASE_SERVICE_ROLE_KEY,VERCEL_TOKEN | 23 | 1.0 | 0.0 | 0.0 | 317.0 |
| Production maturity migrate (RLS + refund) | `.github/workflows/production-maturity-migrate.yml` | active | workflow_dispatch | Y | Y | — | NEXT_PUBLIC_SUPABASE_ANON_KEY,NEXT_PUBLIC_SUPABASE_URL,POSTGRES_URL,POSTGRES_URL_NON_POOLING,SUPABASE_DB_URL,SUPABASE_SERVICE_ROLE_KEY | 3 | 0.333 | 0.667 | 0.0 | 87.0 |
| Send-line reminder backup | `.github/workflows/send-line-reminder-backup.yml` | active | schedule,workflow_dispatch | Y | Y | — | CRON_SECRET | 10 | 1.0 | 0.0 | 0.0 | 7.0 |
| Verify Production | `.github/workflows/verify-production.yml` | active | push,workflow_dispatch | Y | Y | — | CRON_SECRET,CTO_OUTCOME_SECRET,NEXT_PUBLIC_SUPABASE_URL,SUPABASE_SERVICE_ROLE_KEY | 25 | 0.52 | 0.28 | 0.2 | 534.0 |

### `jerry200176-png/vibe-app-store`

Run window: **180d** · sampled runs: **25**

| Workflow | Path | State | Triggers | Timeout | Concurrency | Top perms write | Secrets (names) | 90/180d runs | Success | Fail | Cancel | Median s |
|---|---|---|---|---|---|---|---|---:|---:|---:|---:|---:|
| CI | `.github/workflows/ci.yml` | active | pull_request,push | N | N | — | — | 6 | 0.5 | 0.5 | 0.0 | 16.0 |

