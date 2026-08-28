# AllTrue Workflow Retirement Matrix — 2026-07-27

**Mode:** AUDIT_ONLY — no bulk disable/delete (Founder decision).

Sunrise Autonomous Loop: keep **disabled** (out of this table).

| Workflow file | Purpose (inferred) | Triggers | Last success (sample window) | Last attempted | Secrets (names) | Prod mutation? | Replacement | Runbook ref | Recommended state |
|---|---|---|---|---|---|---|---|---|---|
| `.github/workflows/1387-db-password-rotation.yml` | 1387 DB Password Rotation (Founder-triggered, generates own credential) | workflow_dispatch | no-sample | see Actions UI | PI_HOST,PI_HOST_KEY,PI_SSH_KEY,PI_USER | YES | — | search docs/ops | **MANUAL_ONLY** |
| `.github/workflows/1401-impact-audit.yml` | 1401 Privacy Impact Audit (read-only) | workflow_dispatch | n=1 ok=1.0 | see Actions UI | PI_HOST,PI_HOST_KEY,PI_SSH_KEY,PI_USER | YES | — | search docs/ops | **MANUAL_ONLY** |
| `.github/workflows/173-lr-merge-repair.yml` | In-app | workflow_dispatch | no-sample | see Actions UI | PI_SSH_HOST,PI_SSH_KEY,PI_SSH_USER | YES | — | search docs/ops | **MANUAL_ONLY** |
| `.github/workflows/173-supersede-repair.yml` | In-app | workflow_dispatch | no-sample | see Actions UI | PI_SSH_HOST,PI_SSH_KEY,PI_SSH_USER | YES | — | search docs/ops | **MANUAL_ONLY** |
| `.github/workflows/agent-provenance.yml` | Agent Session Provenance | pull_request | n=67 ok=0.881 | see Actions UI | — | unlikely/read-only | — | search docs/ops | **UNKNOWN_NEEDS_OWNER** |
| `.github/workflows/backup-restore-test.yml` | Backup Restore Verification | schedule,workflow_dispatch | n=1 ok=1.0 | see Actions UI | PI_HOST,PI_HOST_KEY,PI_SSH_KEY,PI_USER | YES | — | search docs/ops | **UNKNOWN_NEEDS_OWNER** |
| `.github/workflows/branch-hygiene.yml` | ⛔ 只讀報告，沒有任何刪除操作 | push,schedule,workflow_dispatch | n=1 ok=1.0 | see Actions UI | — | unlikely/read-only | — | search docs/ops | **UNKNOWN_NEEDS_OWNER** |
| `.github/workflows/bug-detail-dump.yml` | Dump one in-app bug (description/comments/attachments meta + related course prob | push,workflow_dispatch | no-sample | see Actions UI | PI_HOST_KEY,PI_SSH_HOST,PI_SSH_KEY,PI_SSH_USER | YES | — | search docs/ops | **MANUAL_ONLY** |
| `.github/workflows/bug-phase-c-allowlist.yml` | Idempotent Phase C for bugs whose code fix is already on production. | push,workflow_dispatch | no-sample | see Actions UI | PI_HOST_KEY,PI_SSH_HOST,PI_SSH_KEY,PI_SSH_USER | YES | — | search docs/ops | **DISABLE** |
| `.github/workflows/bug-queue-dump.yml` | PII-safe dump of newest open in-app bugs for triage. No writes. | push,workflow_dispatch | no-sample | see Actions UI | PI_HOST_KEY,PI_SSH_HOST,PI_SSH_KEY,PI_SSH_USER | YES | — | search docs/ops | **MANUAL_ONLY** |
| `.github/workflows/bug207-diagnose-push.yml` | Bug 207 Diagnose (push) | unknown | no-sample | see Actions UI | — | unlikely/read-only | — | search docs/ops | **MANUAL_ONLY** |
| `.github/workflows/ci.yml` | ⛔ 此 workflow 只跑測試，絕對不部署任何東西到生產環境 | pull_request,push,workflow_dispatch | n=99 ok=0.596 | see Actions UI | — | YES | — | search docs/ops | **KEEP_ACTIVE** |
| `.github/workflows/classsession-duplicate-diagnose-push.yml` | Read-only Pi diagnose for ClassSession cross-SC / Stop=1 orphans. | push,workflow_dispatch | no-sample | see Actions UI | PI_SSH_HOST,PI_SSH_KEY,PI_SSH_USER | YES | — | search docs/ops | **MANUAL_ONLY** |
| `.github/workflows/codeql.yml` | Security Scan | pull_request,push,schedule | n=93 ok=0.602 | see Actions UI | — | unlikely/read-only | — | search docs/ops | **KEEP_ACTIVE** |
| `.github/workflows/control-plane-enforce.yml` | Control Plane Enforce | pull_request,push | n=53 ok=0.774 | see Actions UI | — | YES | — | search docs/ops | **UNKNOWN_NEEDS_OWNER** |
| `.github/workflows/credential-fingerprint-audit.yml` | Credential Fingerprint Audit (read-only) | workflow_dispatch | no-sample | see Actions UI | PI_HOST,PI_HOST_KEY,PI_SSH_KEY,PI_USER | YES | — | search docs/ops | **MANUAL_ONLY** |
| `.github/workflows/db-password-fingerprint-audit.yml` | DB Password Fingerprint Audit — issue | workflow_dispatch | n=1 ok=0.0 | see Actions UI | PI_HOST,PI_HOST_KEY,PI_SSH_KEY,PI_USER | YES | — | search docs/ops | **MANUAL_ONLY** |
| `.github/workflows/dependency-review.yml` | 與大廠常見「Supply chain / PR 依賴審查」對齊：僅在 PR 上執行，不改 production。 | pull_request | n=67 ok=0.0 | see Actions UI | — | YES | — | search docs/ops | **UNKNOWN_NEEDS_OWNER** |
| `.github/workflows/deploy.yml` | Deploy to Pi | workflow_run | n=20 ok=0.95 | see Actions UI | GITHUB_TOKEN,PI_SSH_HOST,PI_SSH_KEY,PI_SSH_USER,SENTRY_DSN,SMOKE_BRANCH_ID,SMOKE_TEACHER_LOGIN,SMOKE_TEACHER_PASSWORD | YES | — | search docs/ops | **KEEP_ACTIVE** |
| `.github/workflows/docs-integrity.yml` | #543：改為 job-level skip（移除 workflow-level paths 過濾），讓本 workflow 在每個 PR | pull_request,schedule,workflow_dispatch | n=79 ok=0.696 | see Actions UI | — | unlikely/read-only | — | search docs/ops | **UNKNOWN_NEEDS_OWNER** |
| `.github/workflows/dora-metrics.yml` | DORA Metrics Weekly Report | schedule,workflow_dispatch | no-sample | see Actions UI | GITHUB_TOKEN | YES | — | search docs/ops | **UNKNOWN_NEEDS_OWNER** |
| `.github/workflows/high-risk-test-gate.yml` | #736（Review 線 V1）：單人 repo 無第二位強制 reviewer，以「高風險檔強制附測試」 | pull_request | n=80 ok=0.713 | see Actions UI | — | YES | — | search docs/ops | **UNKNOWN_NEEDS_OWNER** |
| `.github/workflows/htaccess-guard.yml` | Execution #481：改 backend/public/.htaccess 必須有 PR label `htaccess-reviewed`， | pull_request | n=80 ok=0.713 | see Actions UI | — | YES | — | search docs/ops | **UNKNOWN_NEEDS_OWNER** |
| `.github/workflows/leave-makeup-evidence-closeout.yml` | Post-merge Pi evidence; waits for deploy HEAD. Never --execute repair. | push,workflow_dispatch | no-sample | see Actions UI | PI_SSH_HOST,PI_SSH_KEY,PI_SSH_USER | YES | — | search docs/ops | **DISABLE** |
| `.github/workflows/mempalace-monthly.yml` | MemPalace Monthly Reminder | schedule,workflow_dispatch | no-sample | see Actions UI | GITHUB_TOKEN | unlikely/read-only | — | search docs/ops | **UNKNOWN_NEEDS_OWNER** |
| `.github/workflows/migration-dryrun.yml` | Execution #476：含 backend/database/migrations/** 變更的 PR， | pull_request | n=11 ok=1.0 | see Actions UI | — | YES | — | search docs/ops | **UNKNOWN_NEEDS_OWNER** |
| `.github/workflows/missing-tests-warn.yml` | Execution #487：當 PR 改了高風險 production code（backend/app/** 或 frontend/src/**） | pull_request | n=79 ok=0.709 | see Actions UI | — | YES | — | search docs/ops | **UNKNOWN_NEEDS_OWNER** |
| `.github/workflows/open-followup-issues.yml` | Cloud agent ghs_ token cannot create Issues (403). Actions GITHUB_TOKEN can | push,workflow_dispatch | no-sample | see Actions UI | GITHUB_TOKEN | YES | — | search docs/ops | **UNKNOWN_NEEDS_OWNER** |
| `.github/workflows/ops-director-leave-hc-pack.yml` | Director leave-HC pack + | push,workflow_dispatch | no-sample | see Actions UI | GITHUB_TOKEN,PI_SSH_HOST,PI_SSH_KEY,PI_SSH_USER | YES | — | search docs/ops | **DISABLE** |
| `.github/workflows/ops-leave-cascade-repair.yml` | Controlled production repair for #1342. | workflow_dispatch | no-sample | see Actions UI | PI_SSH_HOST,PI_SSH_KEY,PI_SSH_USER | YES | — | search docs/ops | **MANUAL_ONLY** |
| `.github/workflows/ops-leave-hc-review-tracker.yml` | Leave-HC campus review tracker (#1342) | push,schedule,workflow_dispatch | n=2 ok=1.0 | see Actions UI | GITHUB_TOKEN,PI_SSH_HOST,PI_SSH_KEY,PI_SSH_USER | YES | — | search docs/ops | **DISABLE** |
| `.github/workflows/ops-leave-vacated-weeks-scan.yml` | Production closeout for KEEP-dates leave (§R82). | workflow_dispatch | no-sample | see Actions UI | PI_HOST,PI_HOST_KEY,PI_SSH_KEY,PI_USER | YES | — | search docs/ops | **MANUAL_ONLY** |
| `.github/workflows/ops-portfolio-td059-leave-audit.yml` | Agent cannot read Issues (App 403). Actions GITHUB_TOKEN can. | push,workflow_dispatch | no-sample | see Actions UI | GITHUB_TOKEN,PI_SSH_HOST,PI_SSH_KEY,PI_SSH_USER | YES | — | search docs/ops | **DISABLE** |
| `.github/workflows/ops-stranded-classify-refresh.yml` | Next autonomous P0/P1 while #1342 waits on directors. | push,workflow_dispatch | no-sample | see Actions UI | GITHUB_TOKEN,PI_SSH_HOST,PI_SSH_KEY,PI_SSH_USER | YES | — | search docs/ops | **DISABLE** |
| `.github/workflows/ops-td059-monitor.yml` | Decision B must be live: periodic FN probe; escalate only on first hit. | push,schedule,workflow_dispatch | no-sample | see Actions UI | GITHUB_TOKEN,PI_SSH_HOST,PI_SSH_KEY,PI_SSH_USER | YES | — | search docs/ops | **DISABLE** |
| `.github/workflows/osv-scanner.yml` | OSS 供應鏈深掃（無需 GitHub Advanced Security）—— #544 | schedule,workflow_dispatch | no-sample | see Actions UI | — | unlikely/read-only | — | search docs/ops | **UNKNOWN_NEEDS_OWNER** |
| `.github/workflows/pi-health.yml` | Pi Health Monitor | schedule,workflow_dispatch | n=2 ok=1.0 | see Actions UI | PI_HOST,PI_HOST_KEY,PI_SSH_KEY,PI_USER,UPTIMEROBOT_API_KEY | YES | — | search docs/ops | **UNKNOWN_NEEDS_OWNER** |
| `.github/workflows/post-audit-issue-comments.yml` | Post audit conclusions to Issues | push,workflow_dispatch | no-sample | see Actions UI | GITHUB_TOKEN | unlikely/read-only | — | search docs/ops | **UNKNOWN_NEEDS_OWNER** |
| `.github/workflows/presubmit.yml` | Google-style presubmit checks — 任何 PR 合進 main 前必須全過 | pull_request | n=79 ok=0.468 | see Actions UI | — | YES | — | search docs/ops | **KEEP_ACTIVE** |
| `.github/workflows/release.yml` | #535 Phase 3.1/3.3 — 在「有 CHANGELOG 變更合併進 main」時，自動建立 CalVer tag + GitHub Release | push,workflow_dispatch | n=10 ok=1.0 | see Actions UI | GITHUB_TOKEN | YES | — | search docs/ops | **UNKNOWN_NEEDS_OWNER** |
| `.github/workflows/repo-governance.yml` | Repo Governance | unknown | no-sample | see Actions UI | — | unlikely/read-only | — | search docs/ops | **UNKNOWN_NEEDS_OWNER** |
| `.github/workflows/rollback-readiness.yml` | #733 — 非破壞性「回滾就緒度」檢查，零 production 風險（全在 CI checkout 內驗）。 | pull_request,schedule,workflow_dispatch | n=12 ok=1.0 | see Actions UI | — | YES | — | search docs/ops | **UNKNOWN_NEEDS_OWNER** |
| `.github/workflows/secret-scan.yml` | Execution #473：在 PR 上跑 gitleaks 阻擋憑證 / .env / pem 進入 main。 | pull_request | n=80 ok=0.713 | see Actions UI | — | YES | — | search docs/ops | **KEEP_ACTIVE** |
| `.github/workflows/slow-query-report.yml` | Slow Query Report | schedule,workflow_dispatch | no-sample | see Actions UI | PI_HOST,PI_HOST_KEY,PI_SSH_KEY,PI_USER | YES | — | search docs/ops | **UNKNOWN_NEEDS_OWNER** |
| `.github/workflows/teacher-signin-diagnose.yml` | Teacher Sign-in Diagnostic (manual) | workflow_dispatch | no-sample | see Actions UI | PI_SSH_HOST,PI_SSH_KEY,PI_SSH_USER | YES | — | search docs/ops | **MANUAL_ONLY** |
| `.github/workflows/teacher-signin-recovery.yml` | Teacher Sign-in Recovery (manual) | workflow_dispatch | no-sample | see Actions UI | PI_SSH_HOST,PI_SSH_KEY,PI_SSH_USER | YES | — | search docs/ops | **MANUAL_ONLY** |
| `.github/workflows/ui-smoke.yml` | #547 / Epic #535 Phase 4.3 起 — 前端 UI smoke（對 production 只讀導航）。 | pull_request,schedule,workflow_dispatch | n=79 ok=0.709 | see Actions UI | SMOKE_BASE_URL,SMOKE_DIRECTOR_PASS,SMOKE_DIRECTOR_USER,SMOKE_TEACHER_PASS,SMOKE_TEACHER_USER | YES | — | search docs/ops | **UNKNOWN_NEEDS_OWNER** |

## Recommended next actions (not executed)
1. Owner review each `UNKNOWN_NEEDS_OWNER` and `DISABLE` candidate.
2. Convert incident/data-repair workflows that still have `push` triggers → `workflow_dispatch` only.
3. Observe 14 days after disable before DELETE_AFTER_OBSERVATION.
4. Keep cost baseline for cancelled Autonomous Loop on Sunrise (770 runs) — do not erase history to claim fix.
