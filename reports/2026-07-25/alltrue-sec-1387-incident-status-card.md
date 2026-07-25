# Incident Status Card — SEC-ALLTRUE-003 / AllTrue issue #1387

Compiled: 2026-07-25 (this session's `/portfolio-maintain triage`, scoped
only to this incident). Supersedes the SEC-ALLTRUE-003 entry in
`state/work-queue.yaml` as last written 2026-07-24 — that entry was stale
on two material points (PR state, CI state) and missing one new finding
(repository visibility). No credential value appears anywhere in this
document.

## Headline

PR #1395 (the code fix) is **already merged** by the Founder
(`jerry200176-png`, 2026-07-24T11:21:13Z, commit `3332d068`) with all 20 CI
checks green. Production is already running a later commit. **The incident
is not closed**: issue #1387 remains open pending operational verification,
and a new, currently-live risk was found during this triage — **the
repository is public right now** — which the carried-forward evidence
believed had been resolved.

## 1. Credential type exposed

A MySQL database password, hard-coded as the CI/test database password for
the `PHPUnit Feature & Unit Tests` job (used in `.github/workflows/ci.yml`'s
`mysql` service definition and duplicated in `backend/phpunit.xml`'s
`DB_PASSWORD` env value). Described in the repo owner's own issue comments
as a value that must be "treated as compromised" and checked for reuse
outside ephemeral CI. Value itself is redacted from this report and was not
reproduced in any evidence file.

## 2. First and last possible exposure time

- **First exposure**: not pinned down by this triage — would require `git
  log -p` / blame on `.github/workflows/ci.yml` and `backend/phpunit.xml`
  to find when the value was first committed. **Unverified — flagged
  below.**
- **Publicly logged**: issue #1387 (filed 2026-07-24T10:30:17Z) cites
  Actions run `30086225720`, job "PHPUnit Feature & Unit Tests," as the log
  that printed the value.
- **Last possible exposure**: ongoing as of this report. The value is
  visible in the pre-fix diff of commit `3332d068` (i.e., recoverable from
  git history at the parent commit and any earlier commit touching those
  two files), and the repository is **currently public** (see §9) — so the
  value is publicly retrievable right now, not just historically.

## 3. Exposure location

- GitHub Actions log: run `30086225720`, job "PHPUnit Feature & Unit
  Tests" (per issue #1387).
- Git history: committed directly in `.github/workflows/ci.yml` (mysql
  service `MYSQL_PASSWORD`) and `backend/phpunit.xml` (`DB_PASSWORD` env),
  confirmed present in the pre-fix version visible in PR #1395's diff.
- **This session's own tool-call transcript**: retrieving PR #1395's diff
  via the GitHub API (necessary to verify the fix) returned the pre-fix
  plaintext value into this session's transcript, since the diff view
  surfaces exactly what git history stores. Not reproduced in this report
  or any file, but worth naming as a concrete instance of "could production
  or transcripts contain the secret" — yes, transiently, in tool output,
  for at least this session.

## 4. Credential revoked / rotated?

**Not confirmed.** No comment on issue #1387 or PR #1395 states that the
actual exposed value was rotated at any point of real use. The remediation
comments describe *replacing the CI config's value* with a deliberately
non-sensitive fixture (`ci-ephemeral`), which is a different claim from
"the old value was rotated wherever it may have been used for real." This
is unlike the earlier, separate incident SEC-ALLTRUE-001 (issue #1007),
where rotation was explicitly confirmed via a named audit run showing the
new TELEGRAM/APP_KEY/BEARER values differ from the leaked ones. No
equivalent confirmation exists for this DB password.

## 5. Old credential confirmed invalid?

**Not confirmed** — same gap as #4. No evidence found that anyone checked
whether the old value works against any real (non-ephemeral-CI) MySQL
instance.

## 6. Git history contains the secret?

**Yes, confirmed.** Visible in the pre-fix state of `.github/workflows/ci.yml`
and `backend/phpunit.xml`, recoverable from any commit before `3332d068`
that touched those files. No history rewrite has occurred (correctly so —
that requires Founder approval per `CLAUDE.md`), so this is expected to
remain true unless the Founder later decides to rewrite history, which
carries its own real risks (collaborator/clone invalidation) and is not
recommended here as a first response.

## 7. GitHub Actions logs/artifacts contain the secret?

**Presumed yes, not independently re-verified.** The originating log (run
`30086225720`) has no recorded evidence of deletion or redaction. GitHub
does not offer a simple "delete this line from a historical log" action;
options are limited (delete the whole workflow run's logs, where
permitted, or accept it as compromised and rotate). No tool available in
this session enumerates or purges Actions log content — this needs a
Founder-directed GitHub UI action if the value ever had real-world reuse
risk. If it's confirmed CI-only and non-reused, this may be an acceptable
residual risk rather than something requiring log deletion.

## 8. Claude transcripts / local logs possibly containing the secret?

**Yes, demonstrated in this very triage** (§3) — the GitHub API diff
fetch surfaced the plaintext value into this session's tool-call
transcript. This is inherent to inspecting a diff that legitimately
contains the value; it wasn't printed in any user-visible output or
written to any file by this session. Whether *other*, prior sessions'
transcripts or local logs also contain it was not checked (out of scope
for this GitHub-only triage) — flagged as unverified.

## 9. Production or third-party abnormal usage evidence?

**Not checked — no tool available in this session for MySQL/production
access logs or the hosting provider's audit trail.** Production HTTP
health/version endpoints were checked (read-only) and show normal
operation:
- `https://daan.lifenet.com.tw/api/v1/health` → `{"status":"ok", ...}` as
  of 2026-07-25T13:05:18+08:00.
- `https://daan.lifenet.com.tw/version.json` → hash `8b4a30f1`, matching
  commit `8b4a30f1` (2026-07-24T14:13:56Z, PR #1412, unrelated to this
  incident) — which is **after** the security fix commit `3332d068`
  (11:21:13Z). The old version-drift concern from the 2026-07-24 evidence
  (production reporting `2e715dd1` while main/deploy targeted `5911a90`)
  appears resolved by subsequent normal deploys; production is now 2
  commits behind current main HEAD (`97f2e611`), which is ordinary deploy
  lag, not a new concern.
- No database-level check (e.g., "does production's real DB_PASSWORD match
  the old exposed value") was performed or is possible with tools
  available in this session.

## 10. New credential storage location & permissions

The CI replacement value `ci-ephemeral` is stored in plaintext directly in
`.github/workflows/ci.yml` (job-level `env:` block) and `backend/phpunit.xml`,
with inline comments marking it "deliberately non-sensitive" and "never
reuse outside ephemeral tests." This is an acceptable pattern **only if**
it is genuinely never reused as a real credential anywhere — which is
exactly what remains unverified (§4, §9).

## 11. Prevention controls

- `gitleaks scan` and `Block secret file types` are present as required CI
  checks and passed on PR #1395 (see §13).
- The original issue's requirement #4 — "add a regression check or
  workflow hardening so environment variables containing PASSWORD, TOKEN,
  SECRET, or KEY are never printed" — has **no confirmed implementation**
  in the merged diff (the diff removes the specific `echo
  "DB_PASSWORD=..." >> $GITHUB_ENV` step, which addresses this one
  instance, but no generic guard against future similar patterns was
  found).

## 12. Corresponding PR

#1395, `fix(ci): remove hard-coded database credential (#1387)`. **Merged**
by `jerry200176-png` at 2026-07-24T11:21:13Z as commit `3332d068`. Base was
`main` at `4479f0f8`.

## 13. CI status

All 20 check runs on PR #1395's head completed successfully at merge time,
including the two the stale evidence claimed were failing:
- Presubmit Checks: success
- Agent Session Provenance: success
- gitleaks scan: success
- PHPUnit Feature & Unit Tests: success
- (Docs Integrity Check and Dependency Review: skipped, not applicable to
  this diff — not failures.)
- Cursor Bugbot: "neutral" — its comments show it repeatedly hit a Cursor
  usage/spend limit and never actually ran on this PR. Not a blocking
  check, but means no Bugbot review occurred.

## 14. Missing production verification

- Confirm the pre-fix value was never used as a real (non-CI) database
  password anywhere reachable from production or staging.
- Confirm no other repository, config, or deployed secret store contains
  the same value (a password reused across services is a realistic risk
  pattern, not checked here).
- Decide whether the originating Actions log (run `30086225720`) needs
  Founder action (delete, or accept as residual risk given CI-only reuse).

## 15. Necessary preconditions before this incident can be closed

1. Founder confirms (or an ops/DB-side check confirms) the exposed value
   was never reused as a real credential — or rotates it wherever it was.
2. Founder decides on the Actions log (§7/§9) — accept as residual risk
   (documented) or take GitHub UI action to remove it.
3. **Founder resolves the repository-visibility discrepancy (§16 below)
   — this is now the most time-sensitive open item, independent of #1387's
   original code fix.**
4. Once 1–3 are resolved, issue #1387 can be closed with evidence (Founder
   action — this session does not close issues).

## 16. Repository visibility — RESOLVED this pass (2026-07-25 ~14:40 +08:00)

**Update, with explicit Founder approval given in this session**: the
repository has been changed from public to private via `gh api -X PATCH
repos/jerry200176-png/AllTrue_System -f private=true`, and the change was
independently re-verified with a fresh `GET` immediately after (`{"private":
true, "visibility": "private"}`). At the same read, forks = 0, releases = 0,
Pages = disabled — no other public mirror/surface of the repository was
found.

Prior to this fix, the repo had been public since at least the prior
triage pass (contradicting an earlier, unverified claim that visibility had
already been restored). Root cause of the earlier discrepancy was not
determined (no audit-log tool available to this session to see who/what
flipped it back to public) — noted as an open question, not a blocker to
closure of *this* specific item.

**This does not retroactively un-expose anything** that was fetched while
the repo was public (see §17–§19 below for what that means in practice).

## 17. Exposure inventory (item C) — locations, with an explicit limitation

**Limitation, stated up front**: this session never captured the actual
exposed credential value in any evidence file or report (by design — see
§3, §8). That means the "exact value" search required by the containment
checklist could not literally be run as a value-grep; instead, this
inventory searches for the *known locations* (file paths, workflow runs)
already identified in §1–§3, plus a broader pattern search on variable
names (`DB_PASSWORD`, `MYSQL_PASSWORD`) to catch anything missed.

- **Branches**: 30 open branches as of this check (`gh api .../branches`),
  none of which touch `.github/workflows/ci.yml` or `backend/phpunit.xml`
  by name (mostly feature/chore branches on unrelated paths). However,
  because Git objects are shared repo-wide, **any branch whose history
  includes a commit before the fix (`3332d068`, 2026-07-24T11:21:13Z) can
  still reach the pre-fix blob** even if the branch tip never touched those
  files — this is a property of the repository's object store, not of
  individual branches, and is not something a per-branch file diff can rule
  out.
- **Tags**: 29 release tags, ranging `v2026.07.19` through `v2026.07.24.6`.
  Tags dated before 2026-07-24T11:21:13Z point at commits whose ancestry
  predates the fix and therefore reach the pre-fix blob via the same
  shared-object-store mechanism above.
- **Code search** (`DB_PASSWORD`/`MYSQL_PASSWORD`, default branch only —
  GitHub's code-search API cannot search across all branches/tags in one
  query): 30 files matched, e.g. `backend/.env.example`,
  `backend/config/database.php`, `docker-compose.yml`,
  `scripts/nightly-backup.sh`, `docs/OPERATIONS_RUNBOOK.md`. **Important
  distinction**: matching on the variable *name* does not mean the actual
  leaked *value* is present — most of these are legitimate references to
  the env-var name in config/docs/example files. Only `.github/workflows/ci.yml`
  and `backend/phpunit.xml` were confirmed (§1, §3) to have contained the
  literal exposed value pre-fix. The other 28 files are flagged as
  **unconfirmed / low-risk** pending a manual check, not as new exposures.
- **Issues/PRs/comments**: no comment text in issue #1387 or PR #1395 was
  found to reproduce the value (checked via the same read that produced
  §12–§13); GitHub's own secret-scanning alert (if AllTrue has one enabled
  for this pattern) was not separately queried in this pass — flagged as
  unverified.
- **Actions logs/artifacts for run `30086225720`** (the run that logged the
  value): job "PHPUnit Feature & Unit Tests" (job id `89458978004`,
  conclusion `failure`) is the source. Two artifacts exist for this run —
  `junit-test-results` (329 bytes) and `frontend-unit-coverage` (533
  bytes) — both are small test-result/coverage summaries, not raw logs;
  **not independently opened/verified in this pass** to confirm they don't
  echo the value, but their small size and stated purpose make that
  unlikely. The raw job log itself (not an artifact — logs and artifacts
  are separate GitHub constructs) is the actual exposure surface and has
  no evidence of deletion or redaction.
- **This session's own tool-call transcript**: as noted in §3/§8, fetching
  PR #1395's diff surfaced the plaintext value transiently in this
  session's tool output. Prior sessions' transcripts/local logs were not
  checked (out of scope for available tools).

**Proposed Actions-log deletion list (proposal only — nothing deleted)**:
- Run `30086225720` (job "PHPUnit Feature & Unit Tests", job id
  `89458978004`) — candidate for log deletion via repo Settings → Actions
  → this run → "Delete logs," **only if** the Founder decides the residual
  risk isn't acceptable. This requires repo-admin action in the GitHub UI
  or an authenticated API call this session has not made and will not make
  unilaterally (destructive, irreversible, explicitly out of scope per
  `CLAUDE.md`).

## 18. Unauthorized-use assessment (item D)

**Confirmed evidence**:
- Repository is now private (§16); current collaborators are
  `jerry200176-png` (admin) and `MonkeyJeng` (push/triage, non-admin) — no
  other accounts currently hold access.
- Forks = 0 at every check this session — no fork-based copy exists via
  GitHub's own fork mechanism.
- Production health/version endpoints show normal operation, no anomalous
  behavior visible from the outside (§9, unchanged from prior check).

**Absence of evidence (not proof of absence)**:
- No sign of anomalous database access, unexpected connections, or
  credential misuse was found — but this session has **no tool access to
  MySQL/database audit logs, the hosting provider's (Raspberry Pi
  self-hosted, per `portfolio.yaml`) access logs, or any WAF/intrusion
  detection system**. A clean read of two public HTTP endpoints is weak
  evidence at best for "no unauthorized use occurred."
- No GitHub audit-log query was run to see who, if anyone, cloned/fetched
  the repository while it was public (GitHub's audit log for clone/fetch
  events on personal-account repos is limited and often not retroactively
  queryable at this access tier — not attempted, flagged as unavailable
  rather than checked-and-clean).

**Unavailable evidence**:
- Any provider-side (hosting, DB) access/audit trail — no tool or
  credential access for this in the current session.
- GitHub's own traffic/clone analytics for the repository (requires
  admin-level API scope not exercised this pass).

**Explicit non-claim**: this session does **not** conclude "no compromise
occurred." It concludes: no positive evidence of compromise was found
within the narrow surfaces this session could check (public HTTP health
endpoints, current collaborator list, fork count), and several higher-value
surfaces (DB/provider audit logs, GitHub audit log) were not checked
because no tool grants access to them.

## 19. History-cleanup impact assessment (item E) — assessment only, no rewrite performed

- **Affected refs**: per §17, every tag dated before 2026-07-24T11:21:13Z
  (up to `v2026.07.24.6`, need to confirm exact cutoff tag-by-tag) and any
  branch whose history predates the fix commit — in practice, this is
  **most of the repository's history**, not an isolated set of refs. A
  targeted rewrite (e.g., `git filter-repo` on just the two known files)
  would still need to touch every ref that reaches the pre-fix commits,
  which based on the branch/tag inventory above is effectively all of them.
- **PR impact**: rewriting history would invalidate the SHAs referenced by
  every closed/merged PR in the repository's history (issue/PR cross-links
  that cite specific commit SHAs would no longer resolve to the rewritten
  tree), and would break any locally-checked-out clones (including this
  portfolio-ops repo's own carried-forward evidence, which cites commit
  SHAs like `3332d068`, `8b4a30f1`, `eacf960f`).
- **Fork/clone recontamination risk**: currently low — forks = 0 (§16,
  §18) — but **any existing local clone** (e.g., collaborator
  `MonkeyJeng`'s machine, or any CI runner cache) that already has the
  pre-fix commits would still contain them after a server-side history
  rewrite, and could recontaminate the remote on a future push unless
  explicitly re-synced. This session did not and cannot inventory local
  clones outside its own tool scope.
- **CI/deployment SHA dependencies**: `portfolio.yaml`/`work-queue.yaml`
  and production version-tracking (`version.json` reporting a `hash`
  field) depend on specific commit SHAs remaining stable and resolvable;
  a history rewrite would break that traceability unless every downstream
  record were updated in lockstep.
- **Recommendation**: **do not rewrite history** as a first response. Now
  that the repository is private (§16) and the credential's *forward* use
  is remediated (§12–§13), the primary residual risk is retrospective (was
  the value ever real/reused — §4/§5, still unconfirmed) rather than
  ongoing public exposure. History rewrite should only be considered if
  credential-reuse verification (§4/§5) comes back positive (the value was
  real and used somewhere) **and** rotation there is also impossible for
  some reason — at which point the cost (broken SHAs, clone
  recontamination risk, PR-history invalidation) may become acceptable
  against a confirmed live-compromise finding. This is a recommendation for
  the Founder's next decision, not an action taken.

## 20. Credential closure — updated 2026-07-25 ~16:20 +08:00 (Founder-approved this session)

**DB provider / environment / consumers, identified**:
- MySQL, self-hosted on the Raspberry Pi, reachable at `127.0.0.1` from the
  backend process (not exposed externally).
- Production credential lives **only** in `/home/admin/backend/.env` on the
  Pi (`DB_PASSWORD`), read by `backend/config/database.php`
  (`env('DB_PASSWORD', '')`) — it is **not** a GitHub Actions secret and
  never has been; `deploy.yml`'s backup step reads it directly off the Pi's
  `.env` file at backup time (`grep DB_PASSWORD .../env | cut -d= -f2`),
  it does not inject it from GitHub.
- The leaked value (pre-fix, in `.github/workflows/ci.yml` / `backend/phpunit.xml`)
  was a **hard-coded literal**, not sourced from any GitHub Actions secret.
  The repo does have a `CI_DB_PASSWORD` repository secret, but the repo's
  own `docs/OPERATIONS_RUNBOOK.md` (§ secret table) documents it as already
  retired — "已退役；active workflows 不引用此 secret" — confirmed:
  `ci.yml`/`phpunit.xml` post-fix both use the literal `ci-ephemeral`, not
  `secrets.CI_DB_PASSWORD`. **No GitHub secret rotation is needed or
  applicable to the leaked value** — there was never a live secret backing
  it.

**Old value reuse/validity — attempted, not yet resolved**:
The repo's own Secret Rotation Policy (`OPERATIONS_RUNBOOK.md` §O) requires
this exact question to be answered *before* rotating: is the exposed value
the same as the real production password? This session built the tool to
answer it the same safe way SEC-ALLTRUE-001 answered the equivalent
question for APP_KEY/TELEGRAM/BEARER (fingerprint comparison, value never
printed): PR
[jerry200176-png/AllTrue_System#1414](https://github.com/jerry200176-png/AllTrue_System/pull/1414)
(Draft, not merged — this session does not merge product-repo PRs), which
adds a `DB_PASSWORD` extraction pattern to
`scripts/credential-fingerprint-audit.py` (tested, 4/4 tests pass, only
synthetic fixture values in the diff) and a new
`db-password-fingerprint-audit.yml` `workflow_dispatch` workflow that
hashes the pre-fix blob value and production's live
`config('database.connections.mysql.password')`, reporting only
`MATCH_ROTATION_REQUIRED` / `DIFFERENT` / `*_NOT_FOUND`.

**Blocked on a GitHub platform constraint, not a policy choice**:
`workflow_dispatch`-triggered workflows must exist on the repository's
*default* branch before GitHub will run them via API/CLI — running them
against another ref's copy of the file is not possible until the workflow
file itself is on `main`. That requires either merging PR #1414 (outside
this session's approval scope for product repositories) or a direct push
to `main` (forbidden — Git rules, branch protection). **This sub-step
cannot be completed from this session regardless of further approval; it
needs the Founder to merge PR #1414 (or otherwise get the workflow onto
`main`) and then run it.**

**Update 2026-07-25 ~17:00 — independent review completed, merge attempted,
found a second, genuine blocker.** Independently reviewed PR #1414 against
the Founder's checklist (workflow permissions, secret handling, logs/
outputs/artifacts/cache, command injection, error paths, whether results
reveal anything beyond match/no-match):

- Workflow-level `permissions: contents: read` — minimal, no write scope.
- `workflow_dispatch` with no `inputs:` — zero attacker-controlled text
  reaches the workflow; no injection surface (blob SHAs and repo/token
  values are hardcoded or trusted `github.*` context, never event payload
  text like issue/PR body).
- Secrets (`PI_SSH_KEY`, `PI_HOST_KEY`, `PI_HOST`, `PI_USER`, `github.token`)
  are used only to establish the SSH connection and API auth; never echoed.
  No `set -x`/verbose tracing anywhere.
- No `actions/upload-artifact` step exists — nothing is persisted off the
  ephemeral runner. Extracted fingerprints live only in `/tmp/credential-audit/`
  on the runner and are deleted in an `if: always()` cleanup step (redundant
  with the runner's own ephemeral lifecycle, but correct hygiene).
- `compare()`'s only output is `KIND\tSTATUS\tleaked=N\tproduction=M` —
  status is one of `MATCH_ROTATION_REQUIRED` / `DIFFERENT` /
  `*_NOT_FOUND`; never a hash or the credential itself. The `leaked=N`/
  `production=M` counts are a minor, already-precedented (same format used
  for SEC-ALLTRUE-001) piece of metadata beyond strict match/no-match —
  noted, not a blocker, given the repo is private with 2 collaborators.
- `set -euo pipefail` plus explicit `test -s` assertions in every step mean
  a missing/empty result (SSH failure, empty production password, etc.)
  fails the step rather than silently reporting a false negative — correctly
  maps to "unavailable/error," not a masked no-match.
- 4/4 tests re-confirmed passing on the current branch state.

**Verdict: safe to merge on the security/workflow-content dimensions the
Founder asked to check.** However, `gh pr merge` failed with
`mergeStateStatus: BLOCKED` — a **different, legitimate blocker**: the
repository's required "Agent Session Provenance" check
(`.github/workflows/agent-provenance.yml` → `scripts/check-agent-provenance.sh`)
failed. Investigation (reading the check script, not just its verdict)
confirms this is **not a false positive** — it's a genuine, correctly-firing
governance gate requiring every PR to carry either an
`.agent-session/manifest.json` produced by the repo's own `agent-control`
launcher (real `session_id`/`task_id`, worktree under
`/home/jerry/workspace/tasks/alltrue/`, `preflight_result: pass`) or a
`human-authored.json`. This PR's branch was built via an ad hoc `git clone`
into this session's scratchpad, outside that launcher, so it legitimately
has neither. This session declined to fabricate either manifest (would
misrepresent authorship) or force-merge past a check the repo's own policy
marks "admin enforcement" (deliberately strict) without clear authorization
to bypass it specifically.

**Founder decision (given live in this session): merge PR #1414 manually**
(GitHub UI/admin), since bypassing this particular governance gate is a
call for the accountable human, not this session. **PR #1414 remains open,
unmerged, by this session.** Once merged, the next step is unchanged:
`gh workflow run db-password-fingerprint-audit.yml --repo
jerry200176-png/AllTrue_System` from `main`.

**Side finding worth carrying forward**: this same provenance-check
pattern very likely explains Sunrise's recurring "Agent Session Provenance"
CI failures on PR #253 (tracked as `CI-SUNRISE-PROVENANCE` in
`state/work-queue.yaml`) — if Sunrise has an equivalent
`check-agent-provenance.sh`-style gate, that failure is probably also a
correctly-firing control against a non-provenance-tracked PR, not a broken
CI config. Not independently confirmed this pass (out of scope for today's
AllTrue-focused work) — flagged for the next time that item is picked up.

**Safe production rotation, if the audit comes back MATCH**: this session
has no SSH/database tool access at all — not a restriction, a genuine
capability gap (the Pi SSH key exists only as a GitHub Actions secret,
usable only inside a workflow run, not directly by this session). If
rotation turns out to be necessary, the repo's own documented SOP
(`OPERATIONS_RUNBOOK.md` §O.2) is: `MySQL FLUSH PRIVILEGES` + `.env` update
+ deploy, executed only after reading `docs/DANGEROUS_OPERATIONS.md` and
confirming backup/rollback — i.e., it should go through the same
GitHub-Actions-mediated path (a new, tested, Founder-reviewed workflow),
not ad hoc SSH from this session.

## 21. GitHub Security log query (item B)

Attempted the requested query (`action:repo.access
repo:jerry200176-png/AllTrue_System`) via the closest available API
surfaces:
- `GET /users/{username}/settings/security-log` → `404 Not Found`
- `GET /users/{username}/audit-log` → `404 Not Found`
- `GET /orgs/{owner}/audit-log` → `404 Not Found` (not applicable —
  `jerry200176-png` is a personal account, not a GitHub organization)
- `GET /users/{username}/events` → succeeds, but this is the ordinary
  public/private **Events API** (recent pushes, PRs, etc.), not the
  Security log; it has no event type for repository visibility changes
  and no `action:repo.access`-style filtering.

**Conclusion: unavailable evidence.** GitHub's personal-account Security
log (`github.com/settings/security-log`) has no public REST/GraphQL API
equivalent — it is Enterprise Cloud org/enterprise audit-log API only. The
visibility-change actor/timestamp/OAuth-app metadata this item asked for
can only be retrieved by the Founder directly opening
`https://github.com/settings/security-log` and filtering
`action:repo.access repo:jerry200176-png/AllTrue_System` in the browser —
no tool in this session can do this on the Founder's behalf. Root cause of
the earlier public-visibility discrepancy (§16) remains undetermined for
the same reason.

## 22. Actions log deletion (item C) — completed 2026-07-25 ~16:10 +08:00

Evidence recorded before any deletion:
- Run `30086225720`, workflow `ci.yml`, job "PHPUnit Feature & Unit Tests"
  (job id `89458978004`), commit `7dca4ced007adc2a93436dd9d3060ff7c514354a`,
  started `2026-07-24T10:27:24Z`, conclusion `failure`.
- Confirmed present pre-deletion: run metadata (`id`, `status`,
  `conclusion`) readable via API; this session did **not** re-fetch the raw
  log text itself (to avoid re-exposing the plaintext value into this
  session's own transcript a second time, per §3/§8's existing caveat) —
  reliance is on issue #1387's own original report that this run's log
  printed the value, which is the reason this run was targeted for
  deletion in the first place.
- **Artifacts precisely checked, not deleted**: two artifacts existed
  (`junit-test-results`, 329 bytes; `frontend-unit-coverage`, 533 bytes).
  Both downloaded and inspected in this session's scratchpad (not the
  product repo) — actual contents are `api-routes.md` (a route listing)
  and `coverage-summary.json` (a coverage report); neither references
  `DB_PASSWORD`, `MYSQL_PASSWORD`, or `ci-ephemeral` in any form. **No
  secret-shaped content found — both artifacts left untouched**, per the
  Founder's "only delete if it contains the secret" condition.
- **Deletion performed**: `DELETE
  /repos/jerry200176-png/AllTrue_System/actions/runs/30086225720/logs`
  (logs-only endpoint — the whole run was deliberately **not** deleted).
- **Verified inaccessible**: a subsequent `GET .../runs/30086225720/logs`
  and `GET .../jobs/89458978004/logs` both now return `404 Not Found`. The
  run's own metadata (`id`, `status`, `conclusion`) is still readable —
  only the log content was removed, exactly as approved.

## Hook live-proof (item G)

Confirmed live and blocking in this actual session: a `git reset --hard`
attempted in a freshly created, disposable throwaway repository
(`/tmp/.../scratchpad/hook-proof-throwaway`, not a real product or
portfolio-ops repo) was blocked by `guard_bash.py` with `Blocked: git
reset --hard. Forbidden — see CLAUDE.md.` The throwaway repo was deleted
immediately after (created and destroyed entirely within this session's
scratchpad, no product data involved). Separately, the same hook already
fired once live earlier in this session on a real command (a `gh pr
create` call whose PR-body text happened to contain the literal substring
"git reset --hard" as a *description*, not an actual destructive command)
— a false positive worth fixing in `docs/hook-threat-model.md`, but also
independent confirmation the hook is wired in and active this session.

## Merge / closure recommendation

**PR #1395 itself**: already merged; retroactively, it was READY TO MERGE
at merge time (all required checks green, minimal/targeted diff, clear
root cause). No action needed on the PR itself.

**Incident #1387 closure**: **NOT READY TO CLOSE.**

Per the Founder's own explicit closure conditions (item F, this session's
instructions), all five of the following must hold before #1387 closes:

| Condition | Status |
|---|---|
| repo private | ✅ RESOLVED — private, re-verified, 0 forks/releases/Pages (§16) |
| old credential confirmed invalid／unused／rotated | ❌ **NOT MET** — the fingerprint-comparison tool to answer this exists (PR #1414) but cannot run yet (§20 — blocked on a GitHub platform constraint: `workflow_dispatch` requires the workflow file on `main`, which requires either merging a product-repo PR — outside this session's scope — or a direct push to `main` — forbidden) |
| replacement verified | ✅ CI-side: PR #1395 merged, `ci-ephemeral` fixture confirmed live (§12, §13). Production-side: not applicable until the row above resolves whether production even needs a change |
| known Actions log exposure removed | ✅ RESOLVED — run `30086225720`'s logs deleted and verified 404; artifacts precisely checked and left untouched, no secret found (§22) |
| remaining evidence and residual risk documented | ✅ this document, §16–22 |

Four of five conditions are met. The one blocking condition — credential
reuse/invalidation confirmation — is not something this session can force
closed: the verification tool is built, tested, and sitting in a Draft PR;
it needs the Founder to either merge PR #1414 or otherwise get the
workflow onto `main` and trigger it, at which point the comparison result
(match/different, never the value itself) resolves this immediately.

## Decisions Required (Founder-only — not something this session can resolve)

1. **Repository visibility** — ✅ RESOLVED this pass (private, verified).
2. **Merge or otherwise land PR #1414** — the single remaining blocker.
   Once the `db-password-fingerprint-audit.yml` workflow exists on `main`,
   trigger it (`gh workflow run db-password-fingerprint-audit.yml`) and the
   result closes the credential-reuse question definitively without ever
   exposing the value.
3. **GitHub Security log** — this session could not query it
   programmatically (§21, no API surface exists for personal-account
   accounts); if the visibility-change root cause matters, check
   `https://github.com/settings/security-log` directly, filtered
   `action:repo.access repo:jerry200176-png/AllTrue_System`.
4. **Issue #1387 closure** — **NOT READY TO CLOSE** until Decision 2
   resolves; this session does not close issues itself regardless.
5. **Root cause of the visibility discrepancy** — still not determined (no
   audit-log access); tied to Decision 3.
