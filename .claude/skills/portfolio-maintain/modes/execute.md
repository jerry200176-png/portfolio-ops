# Mode: execute

Do the highest-ROI safe work, as Draft PRs. Requires a reasonably fresh
`triage` pass first — if `state/work-queue.yaml` / `portfolio.yaml` look
stale (check `updated_at`/`latest_activity`), run `triage` first.

## Steps

1. Read `../../../state/work-queue.yaml` and each Tier 0/1 project's
   `current_priority`/`next_action` in `../../../portfolio.yaml`.
2. If a project hasn't had a baseline audit yet or it's stale, run
   `checklists/baseline-audit.md` for it first.
3. Pick the single highest-ROI unblocked item per
   `../../../docs/prioritization.md`, in Tier order (0, then 1, then 2).
4. Dispatch `repo-maintainer` for exactly one repository, following
   `checklists/execution-standards.md` in full.
5. Dispatch `evidence-verifier` (plus `ux-reviewer`/`security-reviewer` if
   relevant) to independently check the implementer's claims before calling
   the work done.
6. Update `state/work-queue.yaml` with the outcome (branch, PR link, tests
   run, unverified items) and `CEO_DASHBOARD.md`'s Work Completed and
   Decisions Required sections.
7. Repeat 3–6 for the next item only if context and time budget allow;
   otherwise stop and checkpoint (`../../../docs/evidence-policy.md`).

## Hard limits

- One `repo-maintainer` per repository at a time; never mix repos in a
  branch/PR.
- Draft PR is the finish line. Merge/deploy are Founder decisions.
- If a step needs login/OAuth/secrets/production-data/migration/merge/
  deploy/deletion/force-push, stop and surface it — see `../../../CLAUDE.md`.

## Company operating loop requirements

Before implementation, complete discover -> research -> plan. Research the
specific problem using official or primary material, one mature-company
practice, and a maintained open-source or starred repository; record fit,
license, adoption cost, and the hypothesis in a research decision record.
Link the GitHub plan issue and verification commands. After verification,
record surprises and prevention rules in a learning record or linked issue.
If the item is T0 docs or T1 with automated checks, follow
`docs/verify-retry-loop.md` and attach a verify-retry record before handing
off to `evidence-verifier`. Stall twice or five minutes: stop and ask.
On 收工, follow `docs/session-closeout.md`.
