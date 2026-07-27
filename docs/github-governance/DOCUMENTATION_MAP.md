# Documentation Map — 2026-07

Do **not** impose enterprise doc packs on Tier 3/4 repos.

### `jerry200176-png/AllTrue_System`

| Doc capability | Present |
|---|---|
| README | yes |
| CONTRIBUTING | yes |
| SECURITY | yes |
| CODEOWNERS | yes |
| AGENTS/CLAUDE | yes |
| docs/INDEX | yes |
| CHANGELOG | yes |
| AI_REGRESSION | yes |
| dependabot | yes |
- docs/ entries: 98
- **Risk:** large docs tree — rely on INDEX/SSOT; avoid duplicate runbooks.
- Strength: INDEX + control-plane contract + regression lessons.
- Drift risk: many GUIDE_/RUNBOOK_ files; production evidence sometimes lives in PR comments — prefer durable docs/evidence paths.
- SECURITY.md exists at root and docs/SECURITY.md — confirm single SSOT pointer.

### `jerry200176-png/alltrue_studyplan`

| Doc capability | Present |
|---|---|
| README | yes |
| CONTRIBUTING | no |
| SECURITY | no |
| CODEOWNERS | no |
| AGENTS/CLAUDE | no |
| docs/INDEX | no |
| CHANGELOG | no |
| AI_REGRESSION | no |
| dependabot | no |
- docs/: HTTP 404

### `jerry200176-png/income-statement-app`

| Doc capability | Present |
|---|---|
| README | yes |
| CONTRIBUTING | yes |
| SECURITY | no |
| CODEOWNERS | no |
| AGENTS/CLAUDE | yes |
| docs/INDEX | no |
| CHANGELOG | no |
| AI_REGRESSION | no |
| dependabot | no |
- docs/ entries: 14

### `jerry200176-png/income-statement-app-releases`

| Doc capability | Present |
|---|---|
| README | yes |
| CONTRIBUTING | no |
| SECURITY | no |
| CODEOWNERS | no |
| AGENTS/CLAUDE | no |
| docs/INDEX | no |
| CHANGELOG | no |
| AI_REGRESSION | no |
| dependabot | no |
- docs/: HTTP 404

### `jerry200176-png/korea-trip-plan`

| Doc capability | Present |
|---|---|
| README | yes |
| CONTRIBUTING | no |
| SECURITY | no |
| CODEOWNERS | no |
| AGENTS/CLAUDE | no |
| docs/INDEX | no |
| CHANGELOG | no |
| AI_REGRESSION | no |
| dependabot | no |
- docs/ entries: 25

### `jerry200176-png/portfolio-ops`

| Doc capability | Present |
|---|---|
| README | yes |
| CONTRIBUTING | no |
| SECURITY | no |
| CODEOWNERS | no |
| AGENTS/CLAUDE | yes |
| docs/INDEX | no |
| CHANGELOG | no |
| AI_REGRESSION | no |
| dependabot | no |
- docs/ entries: 6
- Strength: autonomy policy + portfolio.yaml SSOT.
- Gap: no SECURITY.md/CONTRIBUTING/CODEOWNERS; acceptable for private control plane but add minimal SECURITY + last-reviewed.

### `jerry200176-png/student-evaluation`

| Doc capability | Present |
|---|---|
| README | yes |
| CONTRIBUTING | no |
| SECURITY | no |
| CODEOWNERS | no |
| AGENTS/CLAUDE | no |
| docs/INDEX | no |
| CHANGELOG | no |
| AI_REGRESSION | no |
| dependabot | no |
- docs/: HTTP 404
- Gap: README only; `node_modules` committed — documentation cannot fix supply-chain bloat; sanitize or archive.

### `jerry200176-png/sunrise-cafe`

| Doc capability | Present |
|---|---|
| README | yes |
| CONTRIBUTING | yes |
| SECURITY | yes |
| CODEOWNERS | yes |
| AGENTS/CLAUDE | yes |
| docs/INDEX | no |
| CHANGELOG | no |
| AI_REGRESSION | no |
| dependabot | yes |
- docs/ entries: 30
- Strength: ARCHITECTURE/DEPLOYMENT/DECISIONS present.
- Drift risk: DECISIONS.md vs DECISION_LOG.md dual ledgers — consolidate pointer.

### `jerry200176-png/vibe-app-store`

| Doc capability | Present |
|---|---|
| README | yes |
| CONTRIBUTING | yes |
| SECURITY | yes |
| CODEOWNERS | no |
| AGENTS/CLAUDE | yes |
| docs/INDEX | no |
| CHANGELOG | no |
| AI_REGRESSION | no |
| dependabot | no |
- docs/ entries: 3
- Has AGENTS/SECURITY/docs; activity dormant — mark last reviewed.

