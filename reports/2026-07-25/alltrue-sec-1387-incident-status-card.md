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

## 16. New finding this triage: repository is currently PUBLIC

**Not part of the original incident's known facts — found during this
triage and is the most urgent item here.** A live GitHub API check
(`search_repositories`) returned `"private": false` for
`jerry200176-png/AllTrue_System` as of this triage (updated_at
2026-07-24T14:24:26Z). This directly contradicts the 2026-07-24T11:04:33Z
issue comment claiming "repository visibility has been restored to private
and read-back verified." Either:
- visibility was changed back to public after that verification (possibly
  to restore unlimited free GitHub Actions minutes — private repos have
  limited free CI minutes, and an earlier report in this portfolio's
  history noted GitHub Actions capacity exhaustion as a recurring problem
  — this is a plausible but **unconfirmed** hypothesis, not a finding), or
- the original private-restoration was itself reverted or never fully
  took effect.

While public, git history (§6, containing the pre-fix database password)
and all historical commits (including anything related to the earlier,
separately-tracked SEC-ALLTRUE-001 credential incident) are publicly
retrievable. **This session did not change repository visibility** — that
is a GitHub UI/API action explicitly reserved for the Founder under the
current conservative autonomy policy (`governance/AUTONOMY_POLICY.md`).

## Merge / closure recommendation

**PR #1395 itself**: already merged; retroactively, it was READY TO MERGE
at merge time (all required checks green, minimal/targeted diff, clear
root cause). No action needed on the PR itself.

**Incident #1387 closure**: **NOT READY TO CLOSE.**

Evidence: code fix merged and deployed (§12, §13, §9); but rotation/
invalidation of the exposed value is unconfirmed (§4, §5), Actions-log
residual exposure is unresolved (§7), and — independent of the original
incident — the repository is currently public (§16), which is a live,
time-sensitive exposure of all git history, not just this one credential.

## Decisions Required (Founder-only — not something this session can resolve)

1. **Repository visibility** — confirm whether AllTrue should be private,
   and if so, restore it via GitHub UI/settings; if public is intentional
   (e.g., for Actions minutes), accept and document that tradeoff
   explicitly given git history contains a now-superseded but real
   credential value.
2. **Credential reuse verification** — confirm (or arrange someone/some
   process to confirm) the old DB password was never used as a real
   credential outside ephemeral CI; rotate anywhere it was.
3. **Actions log residual exposure** — decide whether to leave
   run `30086225720`'s log as accepted residual risk or take GitHub action
   on it.
4. **Issue #1387 closure** — close it yourself (or explicitly direct this
   session to) once 1–3 are addressed, with the evidence trail above.
