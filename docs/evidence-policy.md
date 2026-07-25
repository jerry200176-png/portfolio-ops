# Evidence policy

## Principle

A claim is not a fact until it's cross-checked against a primary source.
"Issue labeled P0" is a claim. "Reproduced the crash in the current build,
confirmed against a Sentry event from the last 7 days" is evidence.

## Cross-verification requirements

| Signal source | Must be cross-checked against |
|---|---|
| GitHub issue label/priority | Code, tests, CI state, and (if claimed) production evidence — labels alone are never sufficient |
| Gmail user report | Repo/issue/CI/logs for the same symptom; a single unverified email does not justify a code change |
| "Fixed" claim in a closed issue/PR | The actual diff and, where possible, a regression test that would have caught the original bug |
| Production health claim | The live version/health endpoint at time of check, not a cached or historical report |
| "Tests pass" claim | Re-run in this session, not trusted from a stale CI badge or a PR description |
| Reference-repo pattern | Verify the pattern still exists at the referenced commit/tag before proposing adoption |

## What to record

For every finding that feeds a priority decision or a PR:

- Evidence: what was observed, where (file/line, URL, log line, timestamp),
  and how it was obtained (command run, endpoint hit, tool used).
- Root cause: the mechanism, not just the symptom.
- What remains unverified: be explicit — "CI could not run because X" is a
  valid, honest status; a silent gap is not.

## What not to record

- Secret values, credential fragments, full email bodies, or more PII than
  needed to identify the signal (see `docs/security-boundaries.md`).
- Speculative severity ("this is probably P0") without the evidence that
  would justify it — record the uncertainty instead.

## Checkpoint format

Use this whenever context is about to run out or a work session is pausing
mid-task, so state isn't lost to context compaction:

```markdown
## Checkpoint — <repo> — <YYYY-MM-DD HH:MM TZ>

- Task: <one line>
- Evidence gathered: <bullets, with links>
- Decisions made: <bullets>
- Changes made so far: <branch name, commit SHAs, files>
- Tests/CI run: <what, result>
- Blocked on: <Founder decision / missing capability / failing gate>
- Next concrete step: <one line, actionable by the next agent or session>
```

Write checkpoints into the relevant `reports/YYYY-MM-DD/` file or, for an
in-flight product task, into `state/work-queue.yaml` as the item's
`evidence` and `next_action` fields — not only into chat context.
