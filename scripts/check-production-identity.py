#!/usr/bin/env python3
"""Read-only, evidence-derived production identity probe for Tier-0 products."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

import yaml

ROOT = Path(__file__).resolve().parents[1]
SHA40 = re.compile(r"^[0-9a-f]{40}$", re.IGNORECASE)


def fetch_json(url: str, timeout: float = 8.0) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": "portfolio-ops-identity-probe"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("response is not a JSON object")
    return payload


def probe(portfolio: dict, fetch: Callable[[str], dict], now: datetime) -> dict:
    """Classify only what the configured read-only endpoints actually prove.

    VERIFIED means a full source SHA was observed and the health endpoint was
    healthy in this probe. It is independent of the recorded inventory SHA.
    MERGED cannot be inferred from runtime endpoints and is never invented.
    """
    projects = []
    for project in portfolio.get("projects", []):
        prod = project.get("production") or {}
        expected = str(project.get("source_commit") or "")
        row = {
            "id": project["id"],
            "observed_at": now.isoformat(),
            "inventory_source_commit": expected or None,
            "serving_sha": None,
            "health": "UNKNOWN",
            "delivery_state": "UNKNOWN",
            "verification_scope": "runtime_identity_and_health_only",
            "product_acceptance": "UNKNOWN",
            "inventory_match": None,
            "errors": [],
        }
        health_url = prod.get("health_url")
        version_url = prod.get("version_url")
        if health_url:
            try:
                health = fetch(health_url)
                if health.get("status") == "ok" or health.get("ok") is True:
                    row["health"] = "HEALTHY"
                elif "status" in health or health.get("ok") is False:
                    row["health"] = "UNHEALTHY"
            except (OSError, TimeoutError, ValueError, TypeError, KeyError) as exc:
                row["errors"].append(f"health probe failed: {type(exc).__name__}")
        else:
            row["errors"].append("health URL missing")
        if version_url:
            try:
                version = fetch(version_url)
                sha = version.get("build_sha") or version.get("commit") or version.get("hash")
                if isinstance(sha, str) and SHA40.fullmatch(sha):
                    row["serving_sha"] = sha.lower()
                else:
                    row["errors"].append("full source SHA missing from version response")
            except (OSError, TimeoutError, ValueError, TypeError, KeyError) as exc:
                row["errors"].append(f"version probe failed: {type(exc).__name__}")
        else:
            row["errors"].append("version URL missing")

        if row["serving_sha"]:
            row["delivery_state"] = "VERIFIED" if row["health"] == "HEALTHY" else "DEPLOYED"
            if SHA40.fullmatch(expected):
                row["inventory_match"] = expected.lower() == row["serving_sha"]
        projects.append(row)
    return {"generated_at": now.isoformat(), "projects": projects}


def render_markdown(report: dict) -> str:
    rows = [
        "## Production identity (read-only observation)",
        f"Generated: `{report['generated_at']}`",
        "VERIFIED = full runtime SHA plus healthy endpoint in this probe; DEPLOYED = SHA observed, health unverified; UNKNOWN = no full runtime SHA. Product acceptance remains UNKNOWN; MERGED is not inferred from these endpoints.",
        "",
        "| Product | Delivery state | Health | Serving SHA | Inventory SHA | Inventory match |",
        "|---|---|---|---|---|---|",
    ]
    for row in report["projects"]:
        match = "UNKNOWN" if row["inventory_match"] is None else ("YES" if row["inventory_match"] else "NO")
        rows.append(
            f"| {row['id']} | {row['delivery_state']} | {row['health']} "
            f"| `{row['serving_sha'] or 'UNKNOWN'}` "
            f"| `{row['inventory_source_commit'] or 'UNKNOWN'}` | {match} |"
        )
    return "\n".join(rows) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fail-on-unhealthy", action="store_true")
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--github-summary", action="store_true")
    parser.add_argument("--portfolio", type=Path, default=ROOT / "portfolio.yaml")
    args = parser.parse_args(argv)
    portfolio = yaml.safe_load(args.portfolio.read_text(encoding="utf-8"))
    report = probe(portfolio, fetch_json, datetime.now(timezone.utc))
    markdown = render_markdown(report)
    print(markdown, end="")
    if args.json_out:
        args.json_out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if args.github_summary and summary_path:
        with open(summary_path, "a", encoding="utf-8") as summary:
            summary.write(markdown)
    failures = []
    for row in report["projects"]:
        if row["delivery_state"] == "UNKNOWN" or row["health"] != "HEALTHY" or row["inventory_match"] is not True:
            failures.append(f"{row['id']}: {row['delivery_state']}, health={row['health']}, inventory_match={row['inventory_match']}")
    if failures:
        print("\nProduction identity findings:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
    return 1 if args.fail_on_unhealthy and failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
