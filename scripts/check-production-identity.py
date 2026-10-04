#!/usr/bin/env python3
"""Read-only, evidence-derived production identity probe for Tier-0 products."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

import yaml

ROOT = Path(__file__).resolve().parents[1]
SHA40 = re.compile(r"^[0-9a-f]{40}$", re.IGNORECASE)
REPO = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
PENDING_STATES = frozenset({"waiting", "pending", "queued", "in_progress"})


def fetch_json(url: str, timeout: float = 8.0) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": "portfolio-ops-identity-probe"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("response is not a JSON object")
    return payload


def fetch_github(path: str) -> dict | list:
    """Use the existing gh identity; never include CLI stderr or token in reports."""
    completed = subprocess.run(
        ["gh", "api", path], capture_output=True, text=True, check=False, timeout=10
    )
    if completed.returncode:
        raise RuntimeError("GitHub evidence unavailable")
    return json.loads(completed.stdout)


def age_hours(value: str, now: datetime) -> int | None:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            return None
        return max(0, int((now - parsed).total_seconds() // 3600))
    except (AttributeError, TypeError, ValueError):
        return None


def pending_deployment(repo: str, serving_sha: str | None, now: datetime,
                       github_fetch: Callable[[str], dict | list]) -> dict:
    result = {
        "candidate_sha": None,
        "candidate_state": "UNKNOWN",
        "candidate_age_hours": None,
        "protected_blocker": "UNKNOWN",
        "candidate_evidence": None,
        "blocker_evidence": None,
    }
    if not REPO.fullmatch(repo):
        return result
    try:
        deployments = github_fetch(f"repos/{repo}/deployments?per_page=20")
        if not isinstance(deployments, list):
            return result
        production = [d for d in deployments if isinstance(d, dict)
                      and "production" in str(d.get("environment", "")).lower()]
        if not production:
            return result
        latest = max(production, key=lambda d: str(d.get("created_at") or ""))
        sha = latest.get("sha")
        deployment_id = latest.get("id")
        if not isinstance(sha, str) or not SHA40.fullmatch(sha) or not isinstance(deployment_id, int):
            return result
        statuses = github_fetch(f"repos/{repo}/deployments/{deployment_id}/statuses?per_page=20")
        if not isinstance(statuses, list) or not statuses:
            return result
        latest_status = max((s for s in statuses if isinstance(s, dict)),
                            key=lambda s: str(s.get("created_at") or ""), default={})
        state = latest_status.get("state")
        if state not in PENDING_STATES or sha.lower() == serving_sha:
            return result
        result.update({
            "candidate_sha": sha.lower(),
            "candidate_state": state.upper(),
            "candidate_age_hours": age_hours(latest.get("created_at"), now),
            "candidate_evidence": f"https://api.github.com/repos/{repo}/deployments/{deployment_id}",
        })
        if state != "waiting":
            return result
        runs = github_fetch(f"repos/{repo}/actions/runs?head_sha={sha}&status=waiting&per_page=20")
        workflow_runs = runs.get("workflow_runs", []) if isinstance(runs, dict) else []
        waiting = [run for run in workflow_runs if isinstance(run, dict)
                   and run.get("head_sha") == sha and run.get("status") == "waiting"]
        for run in waiting:
            run_id = run.get("id")
            if not isinstance(run_id, int):
                continue
            pending = github_fetch(f"repos/{repo}/actions/runs/{run_id}/pending_deployments")
            if not isinstance(pending, list):
                continue
            for item in pending:
                environment = item.get("environment") or {}
                if environment.get("name") != latest.get("environment"):
                    continue
                if item.get("reviewers"):
                    result["protected_blocker"] = "ENVIRONMENT_REVIEW_REQUIRED"
                    result["blocker_evidence"] = f"https://github.com/{repo}/actions/runs/{run_id}"
                    return result
    except (OSError, subprocess.TimeoutExpired, RuntimeError, ValueError, TypeError, KeyError):
        return result
    return result


def probe(portfolio: dict, fetch: Callable[[str], dict], now: datetime,
          github_fetch: Callable[[str], dict | list] | None = None) -> dict:
    """Classify only what the configured read-only endpoints actually prove.

    RUNTIME_VERIFIED means a full source SHA was observed and the health endpoint was
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
            "inventory_age_hours": age_hours(str(project.get("last_verified_at") or ""), now),
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
            row["delivery_state"] = "RUNTIME_VERIFIED" if row["health"] == "HEALTHY" else "DEPLOYED"
            if SHA40.fullmatch(expected):
                row["inventory_match"] = expected.lower() == row["serving_sha"]
        if github_fetch is not None:
            row.update(pending_deployment(str(project.get("github_repo") or ""),
                                          row["serving_sha"], now, github_fetch))
        else:
            row.update(pending_deployment("", row["serving_sha"], now, lambda _: []))
        projects.append(row)
    return {"generated_at": now.isoformat(), "projects": projects}


def render_markdown(report: dict) -> str:
    rows = [
        "## Production identity (read-only observation)",
        f"Generated: `{report['generated_at']}`",
        "RUNTIME_VERIFIED = full runtime SHA plus healthy endpoint in this probe; DEPLOYED = SHA observed, health unverified; UNKNOWN = no full runtime SHA. Product acceptance remains UNKNOWN; MERGED is not inferred from these endpoints.",
        "",
        "| Product | Runtime state / SHA | Inventory age / match | Pending candidate / age | Protected blocker | Product acceptance |",
        "|---|---|---|---|---|---|",
    ]
    evidence = []
    for row in report["projects"]:
        match = "UNKNOWN" if row["inventory_match"] is None else ("YES" if row["inventory_match"] else "NO")
        rows.append(
            f"| {row['id']} | {row['delivery_state']} / `{row['serving_sha'] or 'UNKNOWN'}` "
            f"(observed {row['observed_at']}) | "
            f"{row['inventory_age_hours'] if row['inventory_age_hours'] is not None else 'UNKNOWN'}h / {match} "
            f"(`{row['inventory_source_commit'] or 'UNKNOWN'}`) | "
            f"`{row['candidate_sha'] or 'UNKNOWN'}` / "
            f"{row['candidate_age_hours'] if row['candidate_age_hours'] is not None else 'UNKNOWN'}h "
            f"({row['candidate_state']}) | {row['protected_blocker']} | {row['product_acceptance']} |"
        )
        if row["candidate_evidence"]:
            evidence.append(f"- {row['id']} candidate: {row['candidate_evidence']}")
        if row["blocker_evidence"]:
            evidence.append(f"- {row['id']} blocker: {row['blocker_evidence']}")
    if evidence:
        rows.extend(["", "Evidence:", *evidence])
    return "\n".join(rows) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fail-on-unhealthy", action="store_true")
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--github-summary", action="store_true")
    parser.add_argument("--portfolio", type=Path, default=ROOT / "portfolio.yaml")
    args = parser.parse_args(argv)
    portfolio = yaml.safe_load(args.portfolio.read_text(encoding="utf-8"))
    report = probe(portfolio, fetch_json, datetime.now(timezone.utc), fetch_github)
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
