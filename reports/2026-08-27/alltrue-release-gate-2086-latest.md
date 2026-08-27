# AllTrue PR #2086 latest release gate — 2026-08-27

## Read-only result

At 2026-08-27 11:10:39 +08:00, the formal release evidence check used the
latest PR head `cfc5a1f612d2686e15c166bd9c7f7fcfb6d32663`.

- Health: HTTP 200, `ok=true`.
- Serving build: `5e6598052299386bbf13e12ae320b90186022348`.
- Expected PR #2086 head: `cfc5a1f612d2686e15c166bd9c7f7fcfb6d32663`.
- Version match: **no**.
- Release gate: **FAIL — the latest booking fix is not deployed**.

The latest product CI run `33035364530` completed successfully, including
PHPUnit Feature & Unit Tests, Vite Frontend Build, and the UI regression
workflow. The PR remains open and still needs independent review before any
merge or deployment.

This was a read-only check. It did not change attendance, billing, schedule,
account, or deployment state.
