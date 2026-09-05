#!/usr/bin/env python3
"""Read-only production identity probe for Tier-0 products."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def fetch_json(url: str, timeout: float = 8.0) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": "portfolio-ops-identity-probe"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fail-on-unhealthy", action="store_true")
    args = parser.parse_args()
    portfolio = yaml.safe_load((ROOT / "portfolio.yaml").read_text(encoding="utf-8"))
    failures: list[str] = []
    rows: list[str] = [
        "## Production identity",
        "",
        "| Product | Health | Serving identity | Inventory source_commit | Match |",
        "|---|---|---|---|---|",
    ]
    for project in portfolio.get("projects", []):
        prod = project.get("production") or {}
        health_url = prod.get("health_url")
        version_url = prod.get("version_url")
        expected = str(project.get("source_commit") or "")
        health_ok = False
        serving = "unknown"
        try:
            health = fetch_json(health_url) if health_url else {}
            health_ok = health.get("status") == "ok" or health.get("ok") is True
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, TypeError) as exc:
            failures.append(f"{project['id']} health: {exc}")
        try:
            version = fetch_json(version_url) if version_url else {}
            serving = str(version.get("build_sha") or version.get("commit") or version.get("hash") or "missing")
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, TypeError) as exc:
            failures.append(f"{project['id']} version: {exc}")
            serving = "error"
        identity_unknown = serving in {"unknown", "error", "missing"}
        match = False if identity_unknown else bool(expected and (serving.startswith(expected[:8]) or expected.startswith(serving[:8])))
        identity_result = "UNKNOWN" if identity_unknown else ("yes" if match else "NO")
        if expected and not identity_unknown and not match:
            failures.append(f"{project['id']} identity mismatch inventory={expected} serving={serving}")
        rows.append(
            f"| {project['id']} | {'ok' if health_ok else 'FAIL'} | `{serving}` | `{expected}` | "
            f"{identity_result} |"
        )
        if args.fail_on_unhealthy and not health_ok:
            failures.append(f"{project['id']} unhealthy")
    print("\n".join(rows))
    if failures:
        print("\nFailures:", file=sys.stderr)
        for item in failures:
            print(f"- {item}", file=sys.stderr)
        return 1 if args.fail_on_unhealthy else 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
