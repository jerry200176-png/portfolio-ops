# SEC-ALLTRUE-003 — Independent database credential-rotation review

**Verdict: not-ready.** This is a P0 compromise: production must be treated as reachable with the exposed credential until the old authentication principal is invalidated. No credentials, hashes, fingerprints, database rows, or personal data are included here.

## Audit limits and evidence standard

This review was limited to read-only access and made no production connection or repository change. The repository command environment did not complete even trivial read-only commands during this review; consequently, I cannot responsibly label any repository consumer as verified. The statements below distinguish confirmed scope from deployment facts that Claude must establish from checked-out files and deployed configuration before executing.

Existing incident reports may be used as supporting evidence, but must not substitute for current configuration inspection. In particular, compare deployed secrets/configuration with the effective running revision, not merely the default branch.

## Database engine and authentication model

**Engine: unverified.** Determine from the effective Laravel `DB_CONNECTION` value and infrastructure/runbook configuration. Do not infer MySQL/MariaDB/PostgreSQL from file names or a historical report.

**Authentication model: unverified.** Establish whether the application authenticates with a database-native username/password, IAM/token/certificate authentication, a proxy, or a managed-service identity. Issue #1387 confirms a password remains relevant, but does not by itself identify the engine, account host scope, TLS enforcement, or proxy behavior.

## Consumers

### Verified consumers

None could be verified from repository files in this independent audit because the local read-only command runner was unavailable. The following is a mandatory evidence checklist, not an assertion that each exists.

### Mandatory consumer discovery before rotation

Search the effective repository, deployment secret mappings, generated deployment manifests, and operational jobs for the configuration names `DB_HOST`, `DB_PORT`, `DB_DATABASE`, `DB_USERNAME`, `DB_PASSWORD`, connection URLs/DSNs, `DATABASE_URL`, and provider-specific aliases. Redact values in the evidence record.

| Consumer / location | Evidence Claude must collect | Stale-credential risk |
|---|---|---|
| Laravel web application | `config/database.php`, environment injection, release procedure | config cache, PHP-FPM/opcode processes, persistent PDO connections |
| Laravel queue workers | Supervisor/systemd/container manifests, `queue:work`/`queue:listen` commands | long-lived workers retain cached config and existing DB sessions |
| Horizon | Horizon config, service manifest, deploy hooks | master and workers require controlled termination/restart |
| Scheduler | cron/systemd/Kubernetes schedule plus `schedule:run`/`schedule:work` | a long-running scheduler can retain old config |
| One-off/long-running commands | deploy scripts, daemons, imports, ETL, `artisan` wrappers | still running after deployment |
| Web deployment scripts | CI/CD workflows, release hooks, remote scripts | script may run migrations/cache commands with obsolete env |
| Backups/restores | runbooks, provider jobs, cron, external backup agent | independent DB user or old embedded credential |
| Monitoring/health checks | synthetic checks, exporters, dashboards, alert rules | check may use a separate account or falsely report cached app health |
| Admin/reporting/integration jobs | workflows, scheduled automation, server crons | not visible in Laravel source |
| Database proxies/pools | managed DB/proxy/pooler configuration | pooled sessions can outlive password change |

Also inspect non-repository operational configuration: hosting-console environment variables/secrets, server-level environment files, process managers, secret manager versions, infrastructure-as-code state, and manually created schedules. A repository-only search cannot prove absence.

## Cache, restart, and connection retention assessment

Any of the following can retain the prior credential or an already-authenticated connection:

- Laravel `config:cache`; a release with changed environment but old cached configuration is unsafe.
- PHP-FPM/FastCGI workers (and any Octane/RoadRunner/Swoole process) until graceful reload/restart.
- `queue:work`, Horizon, `schedule:work`, custom daemons, and long-running migration/import commands.
- Supervisor/systemd/container orchestration that restarts only some processes or repopulates environment from an old source.
- Existing persistent PDO/proxy/pooler connections. A password update often affects new authentication only; it may not evict existing sessions.
- CI/CD jobs, backup agents, monitoring, and a rollback release that still references the old secret version.

Do not use a single HTTP health endpoint as proof of rotation: it may be served by an old worker, only exercise an existing pooled connection, or not query the database.

## Recommended minimal-downtime rotation sequence

1. **Founder/private operator:** authorize the change window and enter required provider/database-console credentials privately. Confirm the target production environment and current secret source without revealing values in chat, logs, tickets, command histories, or CI output.
2. Establish a verified, restore-tested backup/recovery point and capture operational evidence listed below. Identify DB engine, account host/identity scope, TLS/proxy/pooler behavior, all credential consumers, exact effective privilege grants, and all restart controls.
3. Prefer creating a **new, separately named least-privilege application principal** (where the engine/platform permits) over changing the existing shared password in place. Grant only the application’s evidenced permissions and enforce the existing network/TLS restrictions. Store the new secret through the approved secret mechanism; do not put it in source, workflow YAML, terminal history, or logs.
4. Update every identified application consumer to the new secret version, including web, workers, Horizon, scheduler, deployment automation, backups, monitoring, and integrations. Ensure the new release’s configuration is generated from the new environment and clear/rebuild Laravel configuration cache in the documented release sequence.
5. Roll out/reload application processes in a controlled order: web capacity first with at least one known-good instance retained where supported; then PHP-FPM/long-running app server; then queue/Horizon with drain or documented graceful termination; then scheduler and custom daemons; finally jobs and monitors. Prevent new worker starts from the old secret source.
6. Run the verification matrix while both principals are valid. Verify new connections rather than relying only on existing sessions. Watch error rates, queue backlog/failures, scheduled task execution, connection saturation, and database authentication failures.
7. After the agreed observation period and only when every consumer is proven on the new principal, lock the old account (or revoke login/rotate its password to an unrecoverable operator-held value according to engine practice), terminate its active sessions if safe, and continue monitoring.
8. After the retention/rollback window, revoke all grants and remove the old account; remove all old secret versions and references under the organization’s retention/audit policy. Preserve a non-secret change record.

Changing the existing password in place has fewer account changes but creates a simultaneous-update requirement for every consumer and makes attribution/rollback weaker. It is acceptable only if a second principal is technically impossible and a proven maintenance window covers all consumers. A second account is the safer P0 response because it permits staged verification and unambiguous old-account detection.

## Required privileges

Exact grants are **unverified** and must be derived from application behavior and existing grants, not guessed. Typical Laravel requirements may include schema/table-level `SELECT`, `INSERT`, `UPDATE`, `DELETE`, and possibly `CREATE`, `ALTER`, `DROP`, `INDEX`, `REFERENCES`, or routine/sequence privileges for migrations. These are not blanket recommendations.

Production runtime should ordinarily have only the data-access permissions actually evidenced. If migrations are run from the application credential, separate migration execution from runtime access if feasible; otherwise document the exceptional DDL privileges, narrow their scope, and remove them after migration. Do not grant administrative, user-management, replication, backup, superuser, or cross-database privileges unless a named operational component demonstrably requires them.

## Backup evidence required before rotation

- A recent completed backup/snapshot for the correct production database, with time, scope, retention, and encryption/access ownership recorded without secret material.
- A successful restore test or a documented, recent restore verification that covers the needed recovery point and application compatibility.
- Database size/object coverage, point-in-time-recovery/log coverage where applicable, and a recovery-time/recovery-point assessment.
- Confirmation that backup jobs themselves will remain functional after rotation and their authentication source is inventoried.
- A named human authorized to approve restoration; rotation rollback is not a substitute for data recovery.

## Verification matrix

| Area | Required test | Pass criterion | Evidence (redacted) |
|---|---|---|---|
| Credential source | Inspect each deployment/process secret reference | every known consumer references the new approved secret version | change record and consumer list |
| Web health | Execute documented liveness and DB-dependent readiness check through a newly restarted instance | application responds and DB-dependent check succeeds | timestamped result/status only |
| Read path | Exercise a non-PII representative read via application | expected response without auth/DB errors | request ID/status only |
| Write path | Perform an approved reversible non-PII transaction in a controlled test path | commit and subsequent read succeed; cleanup verified | test identifier/status only |
| Queue | Enqueue and complete an approved non-PII job on newly restarted workers | completion, no auth failures, normal backlog | job class/status only |
| Horizon/workers | Verify all worker pools are from the new release/config | no old-worker PIDs/pods and normal throughput | process/version counts |
| Scheduler | Trigger/observe one approved scheduled task after restart | exactly one expected execution, no auth error | task name/time/status |
| Long-running tasks | Inventory and restart/drain each daemon | none retain old config/session | service checklist |
| DB sessions | Inspect safely through authorized operator tools | new application sessions use new principal; old principal has none before lock | counts/identity labels only; no rows |
| Backups/monitoring | Run/observe approved checks/jobs | each succeeds with intended identity | status/time only |
| Observability | Monitor app/DB auth errors and saturation during observation window | no correlated regression | aggregate metrics only |

## Rollback matrix

| Failure point | Safe rollback | Trap / guardrail |
|---|---|---|
| New account cannot authenticate | keep old account enabled; revert only affected consumer secret reference; restart that consumer | do not delete or lock old account before end-to-end validation |
| Web release fails after config change | roll web instances to known-good release and its matching old secret source | cached config can make code/secret versions mismatch |
| Workers/Horizon fail | stop intake or drain per documented procedure; restore their matching release/secret; restart cleanly | blindly killing workers may duplicate/loss jobs depending on queue semantics |
| Scheduler fails | revert scheduler deployment/config and ensure no overlapping scheduler runs | two schedulers can double-run jobs |
| Backup/monitoring fails | restore those jobs’ approved prior auth path while old account remains enabled | do not leave a silent backup gap |
| Database load/auth storm | halt rollout, retain already working capacity, investigate pool/retry behavior | automatic retries can overwhelm DB and mask root cause |
| Old account locked too early | temporary re-enable only under named human approval, then fix all consumers | unlocking indefinitely recreates the P0 exposure |
| Data/schema incident | follow separate backup/restore incident procedure | credential rollback cannot undo writes or migrations |

## Fingerprint-audit cautions

Post-rotation fingerprint or secret-scanning audit can mislead when it scans only the current branch, excludes Git history/artifacts/caches, misses encrypted secret stores or provider configuration, or reports a transformed/encoded value as absent. Conversely, a match can be from a deliberately retained incident-evidence record, test fixture, backup, build cache, or old secret version and does not prove a running consumer. Never publish fingerprints or hashes in the audit output. Treat the audit as an inventory aid; proof of containment is the old principal being unable to authenticate plus all approved consumers operating on the new principal.

## Race conditions and rollback traps

- A consumer can start between secret update and restart from an old environment source.
- Existing persistent/pooler sessions can hide broken new authentication until later reconnection.
- Autoscaling can create a new old-config worker after apparently successful rollout.
- A rolling deploy can mix code/config cache/secret versions across instances.
- Queue retry/visibility timeouts can cause duplicated work during worker drain/restart.
- Scheduler overlap can double-charge, double-send, or double-process work; use the established single-scheduler/locking mechanism.
- Migrations may be irreversible or require DDL privilege not granted to the new runtime account; validate privilege and rollback separately.
- Secret propagation delay, provider version pinning, and CI runner cache can cause a deployment to consume an earlier version.
- Revoking the old principal before backup, monitor, or out-of-band integration testing removes the simplest low-impact rollback path.
- Reusing the old account name/password path obscures which consumers actually rotated and weakens detection.

## Founder-only / private-human actions

These require the Founder or a separately authorized private operator, never chat, source control, ticket comments, or CI logs:

1. Authenticate to the production provider/DB/secret manager and approve the production change window.
2. Create, store, and enter credentials or provider-secret values through the approved private console/workflow.
3. Approve account grants, account locking/session termination, rollback re-enablement, and final deletion.
4. Confirm backup/restore authorization and invoke any production restore or provider-side action.
5. Approve any change that impacts customer traffic, maintenance mode, data writes, or external integrations.

Claude Code may prepare redacted commands/checklists and inspect local files; it must not receive or handle secret values.

## Existing Claude plan — independent comparison

No Claude plan artifact was available to this review, so no direct disagreement can be substantiated. The following elements are mandatory and should be added if absent: an effective-deployment (not source-only) consumer inventory; explicit database engine/account-host/TLS/proxy verification; a separate runtime least-privilege principal; cache and long-running-process restart coverage; backup restore evidence; a proof based on new connections; staged old-account lock then deletion; and an approved rollback window that does not reintroduce the compromised secret.

## Final assessment

**not-ready.** Rotation should not begin until the unverified engine/authentication model, effective consumer inventory, exact least-privilege grants, restart ownership, backup/restore evidence, and Founder-approved production controls are documented. Once those gates are met, the staged new-account sequence above is the recommended minimal-downtime approach.
