# Permission Gaps — 2026-07

App installation permissions currently granted (token mint response):
`actions:write`, `administration:read`, `checks:read`, `contents:write`, `deployments:write`, `environments:read`, `issues:write`, `metadata:read`, `pull_requests:write`, `statuses:read`, `workflows:write`.

Credential exposure: **NO**. No secret values read.

## Blocked / limited capabilities

| Permission needed | R/W | Scope | Blocked endpoint pattern | HTTP | X-Accepted-GitHub-Permissions | Why needed | What is missed without it |
|---|---|---|---|---:|---|---|---|
| `security_events` | read | installation (all repos) | `GET /repos/{repo}/code-scanning/alerts` | 403 | `security_events=read` | Verify CodeQL/code scanning alert hygiene for Tier 0 | Cannot confirm open/fixed scanning alerts; security baseline incomplete |
| `secret_scanning_alerts` | read | installation | `GET /repos/{repo}/secret-scanning/alerts` | 403 | `secret_scanning_alerts=read` | Confirm secret scanning posture / open alerts | Blind to secret-scanning alert backlog |
| `vulnerability_alerts` | read | installation | `GET /repos/{repo}/dependabot/alerts` | 403 | `vulnerability_alerts=read` | Dependabot alert triage for production repos | Cannot measure vuln debt or stale critical alerts |

## Non-gaps (do not request admin write)

| Observation | Interpretation |
|---|---|
| Classic branch protection 404 with `administration=read` accepted | Feature absent (rulesets used instead on AllTrue) — **not** a permission gap |
| `GET /user` 403 | Expected for GitHub App installation tokens |
| portfolio-ops `git clone` HTTPS “not found” while Contents/Git Data API works | Operational auth/git path issue; contents:write already sufficient for control-plane commits via API. Do **not** request broader admin. Prefer Git Data API or fix git credential helper. |
| Repository `permissions` object all false on portfolio-ops via API | Known App token quirk; actual Contents/Issues/PR writes succeeded for branch create |

## Explicitly NOT requested
- Administration: write
- Secrets/Variables write
- Members/collaborators write
- Bypass actors / ruleset write

