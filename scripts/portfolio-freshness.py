#!/usr/bin/env python3
"""Report portfolio inventory and evidence freshness without mutating state."""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def parse_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def load_report(now: datetime) -> dict:
    portfolio = yaml.safe_load((ROOT / "portfolio.yaml").read_text(encoding="utf-8"))
    freshness = portfolio.get("freshness", {})
    status_ttl = timedelta(hours=freshness.get("status_ttl_hours", 24))
    evidence_ttl = timedelta(hours=freshness.get("p0_evidence_ttl_hours", 24))
    inventory_ttl = timedelta(days=freshness.get("inventory_ttl_days", 7))

    updated_at = parse_time(str(portfolio["updated_at"]))
    projects = []
    for project in portfolio.get("projects", []):
        verified_at = parse_time(str(project["last_verified_at"]))
        evidence_expires = parse_time(str(project["evidence_expires_at"]))
        p0 = int(project.get("open_p0", 0))
        projects.append({
            "id": project["id"],
            "last_verified_at": project["last_verified_at"],
            "evidence_expires_at": project["evidence_expires_at"],
            "status_stale": verified_at + status_ttl <= now,
            "evidence_stale": evidence_expires <= now,
            "p0_evidence_stale": p0 > 0 and evidence_expires <= now + evidence_ttl,
            "source_commit": project.get("source_commit"),
        })
    return {
        "generated_at": now.isoformat(),
        "inventory_updated_at": portfolio["updated_at"],
        "inventory_stale": updated_at + inventory_ttl <= now,
        "projects": projects,
    }


def render_markdown(report: dict) -> str:
    lines = [
        "## Portfolio freshness",
        f"Generated: `{report['generated_at']}`",
        f"Inventory stale: **{'YES' if report['inventory_stale'] else 'NO'}**",
        "",
        "| Project | Status stale | Evidence stale | P0 evidence warning | Source commit |",
        "|---|---:|---:|---:|---|",
    ]
    for project in report["projects"]:
        lines.append(
            f"| {project['id']} | {'YES' if project['status_stale'] else 'NO'} "
            f"| {'YES' if project['evidence_stale'] else 'NO'} "
            f"| {'YES' if project['p0_evidence_stale'] else 'NO'} "
            f"| `{project.get('source_commit') or 'missing'}` |"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--now", help="UTC/ISO timestamp, useful for deterministic tests")
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--github-summary", action="store_true")
    args = parser.parse_args()
    now = parse_time(args.now) if args.now else datetime.now(timezone.utc)
    report = load_report(now)
    output = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.json_out:
        args.json_out.write_text(output, encoding="utf-8")
    print(render_markdown(report), end="")
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if args.github_summary and summary_path:
        with open(summary_path, "a", encoding="utf-8") as handle:
            handle.write(render_markdown(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
