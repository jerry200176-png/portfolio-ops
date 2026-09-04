# Minimal production observability baseline

**Owner:** portfolio-ops  
**Updated:** 2026-09-04  
**Scope:** read-only fleet checks — not a new monitoring platform.

## Required endpoints (live)

| Product | Health | Version / deploy identity | Status 2026-09-04 |
|---|---|---|---|
| AllTrue | `GET https://daan.lifenet.com.tw/api/v1/health` → `status=ok` | `GET https://daan.lifenet.com.tw/version.json` → `build_sha` | **已存在** — verified `e17d36ba…` / ok |
| Sunrise | `GET https://sunrise-cafe-six.vercel.app/api/booking-health` → `ok=true` | `GET …/api/version` → `commit` | **已存在** — verified `6630b9eb…`; rate_limit **degraded_per_isolate** |

Run: `python scripts/check-production-identity.py`

## Product-owned controls (keep in product repos)

| Control | AllTrue | Sunrise |
|---|---|---|
| Deploy identity after merge | `deploy.yml` + version.json | Vercel + `verify-production.yml` / `npm run production-identity` |
| Audit logs | Schedule/Payroll/StudentIdentity (+ gaps: PIN reset, PII export) — see product `docs/security/AUDIT_LOG_COVERAGE_MATRIX.md` | Ops/reminder observability in app routes |
| Invariants / reconciliation | operations invariants + billing/session reconciliation docs/tests | payment state model + booking health |
| Anomaly detection | **部分存在** (payroll anomalies, scheduler evidence) | **部分存在** (reminder observability); no fleet anomaly bus |

## Intentionally not centralized

Do not build a shared observability framework. Keep audit/invariant semantics
inside each product. Portfolio only stores endpoint URLs, freshness TTL, and
a read-only identity probe.
