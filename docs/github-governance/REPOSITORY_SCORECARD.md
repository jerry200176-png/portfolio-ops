# Repository Scorecard — 2026-07

Scoring is **criticality-proportionate**. Tier 3/4 repos are not expected to carry Tier 0 controls.

| Repo | Tier | Criticality | Runtime/Hosting | Deploy target | Active? | Governance fit | Top gap |
|---|---|---|---|---|---|---|---|
| `AllTrue_System` | Tier 0 | production critical | Raspberry Pi | `.github/workflows/deploy.yml` → daan.lifenet.com.tw | yes | Fit for Tier 0 on paper; cost/noise high; security alert read gap | see remediation |
| `alltrue_studyplan` | Tier 3 | static site／personal tool／prototype | UNKNOWN | workflow main.yml | dormant | Low activity; keep minimal | see remediation |
| `income-statement-app` | Tier 2 | actively developed product | UNKNOWN (app) | release workflow / mirror | low | OK for Tier 2; add timeout/concurrency; clarify prod endpoint if any | see remediation |
| `income-statement-app-releases` | Tier 4 | release mirror／archive candidate | UNKNOWN (app) | release workflow / mirror | low | Likely archive/mirror; confirm purpose then freeze | see remediation |
| `korea-trip-plan` | Tier 3 | static site／personal tool／prototype | GitHub Pages | Pages | yes | Appropriate light CI; delete merged branches; draft PR hygiene | see remediation |
| `portfolio-ops` | Tier 1 | production／business operational | n/a (docs/control) | none | yes | Correct as control plane; needs branch delete-on-merge + minimal CI docs lint | see remediation |
| `student-evaluation` | Tier 3 | static site／personal tool／prototype | static/vite | none observed | dormant | Committed `node_modules` + no CI; archive or sanitize | see remediation |
| `sunrise-cafe` | Tier 0 | production critical | Vercel + Supabase | production-deploy-migrate.yml + Vercel git | yes | Tier 0 product; classic protection present; autonomous loop waste; provenance flaky | see remediation |
| `vibe-app-store` | Tier 3 | static site／personal tool／prototype | GitHub Pages / render.yaml | Pages | low | Dormant; Pages OK; default branch `master` inconsistency vs portfolio | see remediation |

## Per-repo profile
### `jerry200176-png/AllTrue_System`

- **Purpose:** 補習班營運系統；Pi self-host；未成年人 PII + 繳費；deploy.yml → daan.lifenet.com.tw
- **Owner:** jerry200176-png (Founder)
- **Recommended governance tier:** Tier 0
- **Default branch:** `main`
- **Last meaningful commit:** 2026-07-27T03:29:20Z
- **Open Issues / PRs:** 76 / 11
- **Production impact:** HIGH
- **Rulesets:** 1; classic protection HTTP 404
- **Actions enabled:** {'enabled': True, 'allowed_actions': 'all', 'sha_pinning_required': False}

### `jerry200176-png/alltrue_studyplan`

- **Purpose:** 學習計劃相關；低活動；單一 workflow
- **Owner:** jerry200176-png (Founder)
- **Recommended governance tier:** Tier 3
- **Default branch:** `main`
- **Last meaningful commit:** 2026-03-05T17:46:53Z
- **Open Issues / PRs:** 0 / 0
- **Production impact:** LOW
- **Rulesets:** 0; classic protection HTTP 404
- **Actions enabled:** {'enabled': True, 'allowed_actions': 'all', 'sha_pinning_required': False}

### `jerry200176-png/income-statement-app`

- **Purpose:** 損益表 App；有 CI + release workflow；近期仍有 Actions 活動
- **Owner:** jerry200176-png (Founder)
- **Recommended governance tier:** Tier 2
- **Default branch:** `main`
- **Last meaningful commit:** 2026-05-31T14:37:42Z
- **Open Issues / PRs:** 0 / 0
- **Production impact:** MEDIUM
- **Rulesets:** 0; classic protection HTTP 404
- **Actions enabled:** {'enabled': True, 'allowed_actions': 'all', 'sha_pinning_required': False}

### `jerry200176-png/income-statement-app-releases`

- **Purpose:** release artifact mirror；workflow 少、無產品碼跡象
- **Owner:** jerry200176-png (Founder)
- **Recommended governance tier:** Tier 4
- **Default branch:** `main`
- **Last meaningful commit:** 2026-05-31T14:35:22Z
- **Open Issues / PRs:** 0 / 0
- **Production impact:** LOW
- **Rulesets:** 0; classic protection HTTP 404
- **Actions enabled:** {'enabled': True, 'allowed_actions': 'all', 'sha_pinning_required': False}

### `jerry200176-png/korea-trip-plan`

- **Purpose:** 個人行程 handbook（Astro/Pages）；非營運關鍵
- **Owner:** jerry200176-png (Founder)
- **Recommended governance tier:** Tier 3
- **Default branch:** `main`
- **Last meaningful commit:** 2026-07-24T09:02:27Z
- **Open Issues / PRs:** 1 / 1
- **Production impact:** LOW
- **Rulesets:** 0; classic protection HTTP 404
- **Actions enabled:** {'enabled': True, 'allowed_actions': 'all', 'sha_pinning_required': False}

### `jerry200176-png/portfolio-ops`

- **Purpose:** Portfolio control plane（非產品 runtime）；治理與 triage SSOT；private
- **Owner:** jerry200176-png (Founder)
- **Recommended governance tier:** Tier 1
- **Default branch:** `main`
- **Last meaningful commit:** 2026-07-25T23:04:04Z
- **Open Issues / PRs:** 0 / 1
- **Production impact:** MEDIUM
- **Rulesets:** 0; classic protection HTTP 404
- **Actions enabled:** {'enabled': True, 'allowed_actions': 'all', 'sha_pinning_required': False}

### `jerry200176-png/student-evaluation`

- **Purpose:** 前端工具；無 workflow；含 node_modules 於 repo；末次 2026-02
- **Owner:** jerry200176-png (Founder)
- **Recommended governance tier:** Tier 3
- **Default branch:** `main`
- **Last meaningful commit:** 2026-02-07T06:23:46Z
- **Open Issues / PRs:** 0 / 0
- **Production impact:** LOW
- **Rulesets:** 0; classic protection HTTP 404
- **Actions enabled:** {'enabled': True, 'allowed_actions': 'all', 'sha_pinning_required': False}

### `jerry200176-png/sunrise-cafe`

- **Purpose:** 餐廳訂位/訂金/LINE；Vercel+Supabase；公開 repo；production deploy workflow
- **Owner:** jerry200176-png (Founder)
- **Recommended governance tier:** Tier 0
- **Default branch:** `main`
- **Last meaningful commit:** 2026-07-27T00:15:36Z
- **Open Issues / PRs:** 4 / 1
- **Production impact:** HIGH
- **Rulesets:** 0; classic protection HTTP 200
- **Actions enabled:** {'enabled': True, 'allowed_actions': 'all', 'sha_pinning_required': False}

### `jerry200176-png/vibe-app-store`

- **Purpose:** 社群目錄；Pages；低活動（末次 meaningful push 2026-04）
- **Owner:** jerry200176-png (Founder)
- **Recommended governance tier:** Tier 3
- **Default branch:** `master`
- **Last meaningful commit:** 2026-04-05T00:42:12Z
- **Open Issues / PRs:** 0 / 0
- **Production impact:** LOW
- **Rulesets:** 0; classic protection HTTP 404
- **Actions enabled:** {'enabled': True, 'allowed_actions': 'all', 'sha_pinning_required': False}

