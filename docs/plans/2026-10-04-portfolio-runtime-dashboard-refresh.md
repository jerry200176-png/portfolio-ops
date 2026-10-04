# Portfolio runtime dashboard refresh — 2026-10-04

## Goal and scope

Make the public portfolio dashboard point to current, time-stamped production
identity evidence while preserving the distinction between runtime health,
inventory freshness, pending candidate visibility, and product acceptance.

In scope: `CEO_DASHBOARD.md` and one dated, public-safe Markdown/JSON evidence
report under `reports/2026-10-04/`. Reuse `scripts/check-production-identity.py`
and the existing `weekly-governance-report.yml` artifact. Do not change
`portfolio.yaml` freshness timestamps or issue counts because full inventory
triage has not been completed. Do not publish private deployment candidate
SHAs or reviewer data.

## Evidence and current authority

- Portfolio Ops GitHub `main`: `d49596b3f72698a8d545696cebfc6bfc1a5de3ee`
  (2026-10-04).
- Latest scheduled identity artifact: run
  [37174146031](https://github.com/jerry200176-png/portfolio-ops/actions/runs/37174146031),
  generated `2026-10-04T03:28:01Z`. The workflow failed in both freshness
  generation and production identity verification. Public HTTP probes
  returned healthy responses, but the identity gate exited with failure
  because both runtime SHAs differed from stale inventory SHAs.
  The repository-scoped token correctly left candidates and protected blockers
  `UNKNOWN`.
- Fresh direct public endpoint reads at `2026-10-04T08:14:55Z` observed AllTrue
  `e483c1dc43975cfa173b12e75376fa51dc107a30` and Sunrise
  `fec9e458767bd5b4a0e51cb440d4145440591ecc`. Both health endpoints returned
  healthy status in the public-only generated JSON. A separate Sunrise health
  probe at `08:11Z` reported `rate_limit_grade=degraded_per_isolate`. AllTrue
  `deployment.json` checked at `08:11Z` reports backend/frontend SHA
  `e483c1dc...`, source `github-actions:deploy.yml`, and
  `deployed_at=2026-10-03T22:11:33Z`; neither product endpoint exposes an
  artifact digest. The published snapshot includes only public runtime
  identity/health fields; candidates, protected blockers, and product
  acceptance remain `UNKNOWN`.
- `portfolio.yaml` inventory/status timestamps remain `2026-09-04`; a fresh
  runtime observation does not validate stale issue counts or priorities.

## Risk, rollback, and acceptance

Risk: R0, documentation/evidence only; no product code, workflow, credentials,
production data, deployment, or approval policy changes. Rollback is a normal
revert of the documentation commit.

Acceptance:

1. The dashboard prominently shows the freshness state and links to the
   existing automated report.
2. The dated JSON/Markdown report names each public runtime SHA, health,
   observation time, and inventory mismatch; candidate, protected blocker,
   artifact digest, and acceptance are explicitly `UNKNOWN`.
3. Old inventory counts and priorities remain visibly stale until a complete
   triage refresh.
4. `git diff --check`, company/governance contract validators, and the existing
   portfolio freshness ownership check pass. The freshness monitor itself may
   still report stale repository inventory; it must not be weakened to pass.
5. A separate reviewer re-derives the public/private data boundary and reruns
   the documented checks.

## Verification plan

```bash
python3 - <<'PY'
import importlib.util, json
from datetime import datetime, timezone
from pathlib import Path
import yaml

path = Path("scripts/check-production-identity.py")
spec = importlib.util.spec_from_file_location("identity_probe", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
portfolio = yaml.safe_load(Path("portfolio.yaml").read_text(encoding="utf-8"))
report = module.probe(portfolio, module.fetch_json, datetime.now(timezone.utc), github_fetch=None)
Path("/tmp/portfolio-runtime-public-identity.json").write_text(
    json.dumps(report, indent=2) + "\n", encoding="utf-8"
)
PY
curl --fail --silent --show-error --max-time 10 https://daan.lifenet.com.tw/version.json
curl --fail --silent --show-error --max-time 10 https://daan.lifenet.com.tw/deployment.json
curl --fail --silent --show-error --max-time 10 https://daan.lifenet.com.tw/api/v1/health
curl --fail --silent --show-error --max-time 10 https://sunrise-cafe-six.vercel.app/api/version
curl --fail --silent --show-error --max-time 10 https://sunrise-cafe-six.vercel.app/api/booking-health
python3 scripts/portfolio-freshness.py --json-out /tmp/portfolio-freshness-20261004.json
python3 scripts/validate-company-agent-contract.py
python3 scripts/validate-governance-contract.py
python3 scripts/portfolio-freshness.py --changed-paths CEO_DASHBOARD.md,reports/2026-10-04/production-identity-public.md,docs/plans/2026-10-04-portfolio-runtime-dashboard-refresh.md --fail-on-stale-when-inventory-changed
git diff --check
```

The public JSON is built by the reusable probe with `github_fetch=None`, so it
does not make GitHub API calls and candidate/blocker fields remain `UNKNOWN`.
No new tool or paid service is introduced. Learning:
`check-production-identity.py` uses the caller's `gh` identity by default, so
local output can see private deployment metadata that the repository-scoped
Actions job cannot. Public records must use the scoped workflow output or the
probe's public-only mode; never copy privileged local JSON wholesale.
