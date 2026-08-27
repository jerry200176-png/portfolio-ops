# AllTrue PR #2086 release gate — 2026-08-27

## Read-only result

Command:

```text
python3 scripts/release-evidence.py \
  --version-url https://daan.lifenet.com.tw/version.json \
  --health-url https://daan.lifenet.com.tw/api/v1/health \
  --expected-sha 4af00816eb556d41d374b06a2e3de28f1c410a65
```

Result at 2026-08-27 10:53:30 +08:00:

- Health: HTTP 200, `ok=true`.
- Serving build: `5e6598052299386bbf13e12ae320b90186022348`.
- Expected PR #2086 head: `4af00816eb556d41d374b06a2e3de28f1c410a65`.
- Version match: **no**.
- Release gate: **FAIL — PR #2086 is not deployed**.

This was a read-only check. It did not change attendance, billing, schedule,
account, or deployment state. The Portfolio queue remains at
`ready_for_independent_review`; deployment and post-deploy acceptance are
still required before asking the director to retry the workflow.
