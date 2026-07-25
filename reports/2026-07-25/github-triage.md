# GitHub Triage — 2026-07-25

Read-only. Delegated to `github-triage` (AllTrue, Sunrise), no GitHub write
tools used. Scores use `Priority = Impact × Confidence × Urgency ÷ Effort`
(`docs/prioritization.md`). Labels are treated as claims, not ground truth,
per `docs/evidence-policy.md`.

## AllTrue System

### 1. Issue #1401 — Parent-portal cross-student PII exposure (candidate P0)
- **Evidence**: fix PR #1400 is merged. Production-deploy claim is
  self-reported in the issue thread, not independently confirmed by this
  agent (no direct production data access in its tool scope).
- **Containment checklist in the issue itself is entirely unchecked**:
  parent notification, evidence retention, exposure-log review — none
  marked done.
- Impact: high (PII of minors, cross-student data boundary). Confidence:
  medium (code fix confirmed merged; deploy + containment unconfirmed).
  Urgency: high. Effort: low-medium (containment is process, not code).
- **Score rationale**: highest-impact item in the portfolio this pass —
  ranks above SEC-ALLTRUE-003's remaining open items because it's an
  *active* authorization boundary bug (not historical exposure) affecting
  minors' data, and its own remediation checklist is unexecuted.
- Next step: Founder confirms production deploy of #1400 and executes the
  containment checklist items (notification, evidence retention, exposure
  review) — this session does not do so unilaterally (PII/legal-adjacent).

### 2. GitGuardian 3-secret cluster (Telegram Bot Token, Laravel APP_KEY, Bearer Token)
- Flagged 2026-07-17 per Gmail; **not independently confirmed via GitHub
  secret-scanning API in this pass** — the agent could not determine
  whether these are the *same* candidates already addressed under
  SEC-ALLTRUE-001's rotation audit (which confirmed TELEGRAM, APP_KEY, and
  BEARER were different from historical leaked candidates, per
  `state/work-queue.yaml` SEC-ALLTRUE-001 evidence) or a **new, separate**
  set.
- Status: **unresolved-pending-confirmation**. Treated as a candidate
  finding, not scored, until GitHub secret-scanning alerts are pulled
  directly and diffed against the SEC-ALLTRUE-001 rotation-audit set.
- Next step: run `run_secret_scanning` against AllTrue directly and compare
  timestamps/fingerprints to the SEC-ALLTRUE-001 closure evidence before
  this can be prioritized as new work or marked already-covered.

### 3. SEC-ALLTRUE-003 — repo visibility (carried forward, unresolved)
- No change from the prior pass: repo visibility claim ("restored to
  private") remains **unverifiable by this agent's tool scope** (no
  repo-metadata/visibility tool available to `github-triage`). This is the
  same open gap noted in the prior incident status card.
- Still a Founder decision item; see `Decisions Required` in
  `CEO_DASHBOARD.md`.

### 4. Issue #1096 — Billing calculation bug (0/2998 vs 3000)
- Open, no PR attached. Impact: medium (billing correctness, not security).
  Confidence: high (concrete reproducible numeric discrepancy reported).
  Urgency: medium. Effort: low.
- Next step: candidate for next `execute`-mode Draft PR once P0 items clear.

### 5. Issue #1100 — A/B package overlap (decision needed, not a bug)
- This is a product-decision item, not a code defect — needs Founder/PM
  input on intended package behavior before any PR is drafted.
- Next step: leave queued; do not treat as engineering work until decision
  is made.

### PROD-ALLTRUE-003 (PR #1333) — status correction
- **Confirmed MERGED** (commit `eacf960f`, 2026-07-19). Prior
  `work-queue.yaml`/`portfolio.yaml` status of "validating_ci" was stale.
  Corrected in this pass.

## Sunrise Cafe

### 1. Agent Session Provenance CI check — repeated failures
- Confirmed as a real, currently-failing required check on PR #253:
  `preflight_result: cloud-agent-bypass` rejected, plus an out-of-root
  worktree path flagged. Matches the Gmail-reported pattern (8 failures in
  30 days).
- Impact: medium (blocks merges via a governance gate, not a production
  defect). Confidence: high (directly observed on-PR check status).
  Urgency: medium. Effort: unknown — needs log-level triage to tell whether
  this is a broken CI config or a genuine provenance/security gap.
- Next step: pull full check-run logs for PR #253's Agent Session
  Provenance job before deciding whether this is a CI bug or a real policy
  violation worth escalating.

### 2. Issue #211 — decision made, not executed
- Founder decisions FD-1…FD-6 (RLS, rate limiting, backup posture) were
  recorded 2026-07-19. **Zero execution PRs exist since** — confirmed via
  PR search, no matches referencing #211 or its decision items.
- This is a live risk gap, not a queued-but-unstarted item: fail-open rate
  limiting and unconfirmed backup posture are currently in production.
- Next step: candidate for the next `execute`-mode pass — highest-ROI
  Sunrise engineering work available since the decision-making step is
  already done.

### 3. dependabot.yml wildcard change (local uncommitted, `chore/dependabot-major-policy` branch)
- Local working-tree diff widens the major-version ignore list to a
  wildcard (`dependency-name: "*"`). Content **structurally matches** what
  already shipped on `origin/main` via merged PR #249 (2026-07-19); no open
  or closed PR exists for this specific branch.
- Agent could not confirm byte-identity (no `git diff` tool in its scope);
  confirmed separately via direct `git diff` this session — the working
  tree change is not touched or discarded, per Git rules (never
  reset/clean a tree we didn't create).
- Next step: confirm with Founder/orchestrator whether this branch is
  stale/redundant (safe to leave as-is or discard) or represents
  in-progress intent that should continue.

### OPS-SUNRISE-001 — Vercel capacity, CI-signal limitation
- GitHub CI status checks show "Canceled by Ignored Build Step" for recent
  preview attempts — this does **not** by itself confirm the capacity issue
  is resolved or ongoing; the check simply didn't run. Cross-reference with
  Gmail signals below, which show direct production impact.
