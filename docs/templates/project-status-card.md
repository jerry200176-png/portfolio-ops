# Project Status Card — template

One of these per Tier 0/1 project, refreshed by `/portfolio-maintain
execute` baseline audits. Keep it to what fits below — this is a snapshot,
not a wiki page. Store under `reports/YYYY-MM-DD/status-cards/<id>.md`.

```markdown
# <Product Name> — Status Card (<YYYY-MM-DD>)

**Positioning:** <one sentence>
**Primary users:** <who>
**Job-to-be-done:** <what they're trying to accomplish>

## Production
- Status: <live/staged/none> — <version/revision>
- Last deploy: <date, SHA>
- CI: <green/red/blocked — link>
- Health: <endpoint result, timestamp>

## Open work
- Open Issues: <count, link to filtered view>
- Open PRs: <count, link>
- P0: <count and one-line each>
- P1: <count and one-line each>

## Signals
- Gmail (last 90d): <count and top 1-3 with severity>
- Production evidence contradicting or confirming issue claims: <notes>

## Risks
- Top production/reliability risk: <one line + evidence>
- Top UX friction: <one line + evidence>
- Top test/observability gap: <one line + evidence>

## This round
- Highest-ROI next action: <one line, per docs/prioritization.md>
- Founder decisions needed: <bullets, or "none">
```
