#!/usr/bin/env python3
"""Report portfolio inventory and evidence freshness without mutating state.

PR correctness vs operational freshness are separate responsibilities:

* ``--fail-on-stale`` — scheduled/manual monitor and inventory-touching PRs.
* ``--fail-on-stale-when-inventory-changed`` — PR/push gate: block only when
  this change owns live inventory/evidence fields in ``portfolio.yaml``.
  Pre-existing repository-wide staleness must not fail unrelated code PRs.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

# Paths that own the live portfolio freshness contract evaluated by this script.
# Changing any of these means the PR is writing/owning inventory timestamps and
# must pass fail-closed freshness validation.
INVENTORY_OWNERSHIP_PATHS = frozenset(
    {
        "portfolio.yaml",
    }
)

_NULL_OID = "0" * 40


def parse_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def load_report(now: datetime, *, portfolio_path: Path | None = None) -> dict:
    path = portfolio_path or (ROOT / "portfolio.yaml")
    # Local import keeps the module importable in environments without PyYAML
    # until report generation is requested (matches prior script behavior).
    import yaml

    portfolio = yaml.safe_load(path.read_text(encoding="utf-8"))
    freshness = portfolio.get("freshness", {})
    status_ttl = timedelta(hours=freshness.get("status_ttl_hours", 24))
    evidence_ttl = timedelta(hours=freshness.get("p0_evidence_ttl_hours", 24))
    inventory_ttl = timedelta(days=freshness.get("inventory_ttl_days", 7))

    updated_at = parse_time(str(portfolio["updated_at"]))
    projects = []
    any_project_stale = False
    for project in portfolio.get("projects", []):
        verified_at = parse_time(str(project["last_verified_at"]))
        evidence_expires = parse_time(str(project["evidence_expires_at"]))
        p0 = int(project.get("open_p0", 0))
        status_stale = verified_at + status_ttl <= now
        evidence_stale = evidence_expires <= now
        any_project_stale = any_project_stale or status_stale or evidence_stale
        projects.append(
            {
                "id": project["id"],
                "last_verified_at": project["last_verified_at"],
                "evidence_expires_at": project["evidence_expires_at"],
                "status_stale": status_stale,
                "evidence_stale": evidence_stale,
                "p0_evidence_stale": p0 > 0 and evidence_expires <= now + evidence_ttl,
                "source_commit": project.get("source_commit"),
            }
        )
    inventory_stale = updated_at + inventory_ttl <= now
    return {
        "generated_at": now.isoformat(),
        "inventory_updated_at": portfolio["updated_at"],
        "inventory_stale": inventory_stale,
        "any_stale": inventory_stale or any_project_stale,
        "projects": projects,
    }


def render_markdown(report: dict) -> str:
    lines = [
        "## Portfolio freshness",
        f"Generated: `{report['generated_at']}`",
        f"Inventory stale: **{'YES' if report['inventory_stale'] else 'NO'}**",
        f"Any stale: **{'YES' if report['any_stale'] else 'NO'}**",
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


def inventory_ownership_touched(changed_paths: set[str]) -> bool:
    """Return True when the diff owns live inventory/evidence source paths."""
    return bool(changed_paths & INVENTORY_OWNERSHIP_PATHS)


def git_changed_paths(*, diff_base: str, diff_head: str, repo: Path) -> set[str]:
    """Return paths changed between ``diff_base...diff_head`` (merge-base form)."""
    if not diff_base or diff_base == _NULL_OID:
        raise ValueError("diff_base is missing or a null OID; cannot prove inventory untouched")
    proc = subprocess.run(
        ["git", "diff", "--name-only", f"{diff_base}...{diff_head}"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            "git diff failed while detecting inventory ownership changes: "
            f"{proc.stderr.strip() or proc.stdout.strip() or proc.returncode}"
        )
    return {line.strip() for line in proc.stdout.splitlines() if line.strip()}


def resolve_blocking(
    *,
    fail_on_stale: bool,
    fail_when_inventory_changed: bool,
    diff_base: str | None,
    diff_head: str,
    changed_paths: set[str] | None,
    repo: Path,
) -> tuple[bool, str]:
    """Decide whether stale inventory must fail this invocation.

    Returns ``(blocking, reason)``.
    """
    if fail_on_stale and fail_when_inventory_changed:
        raise ValueError(
            "use either --fail-on-stale or --fail-on-stale-when-inventory-changed, not both"
        )
    if fail_on_stale:
        return True, "unconditional --fail-on-stale"
    if not fail_when_inventory_changed:
        return False, "informational only"

    if changed_paths is None:
        if not diff_base:
            raise ValueError(
                "--fail-on-stale-when-inventory-changed requires --diff-base "
                "or --changed-paths"
            )
        changed_paths = git_changed_paths(
            diff_base=diff_base, diff_head=diff_head, repo=repo
        )

    if inventory_ownership_touched(changed_paths):
        touched = sorted(changed_paths & INVENTORY_OWNERSHIP_PATHS)
        return True, f"inventory ownership paths changed: {', '.join(touched)}"
    return False, "inventory ownership paths unchanged; stale state is informational"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--now", help="UTC/ISO timestamp, useful for deterministic tests")
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--github-summary", action="store_true")
    parser.add_argument(
        "--portfolio",
        type=Path,
        help="override portfolio.yaml path (tests)",
    )
    parser.add_argument(
        "--fail-on-stale",
        action="store_true",
        help="exit 1 when inventory or any project status/evidence is stale",
    )
    parser.add_argument(
        "--fail-on-stale-when-inventory-changed",
        action="store_true",
        help=(
            "exit 1 on stale only when this change touches inventory ownership "
            f"paths ({', '.join(sorted(INVENTORY_OWNERSHIP_PATHS))})"
        ),
    )
    parser.add_argument(
        "--diff-base",
        help="git base OID/ref for ownership detection (three-dot vs --diff-head)",
    )
    parser.add_argument(
        "--diff-head",
        default="HEAD",
        help="git head OID/ref for ownership detection (default: HEAD)",
    )
    parser.add_argument(
        "--changed-paths",
        help="comma-separated paths overriding git diff (tests / explicit CI)",
    )
    parser.add_argument(
        "--repo",
        type=Path,
        default=ROOT,
        help="git repository root for ownership detection",
    )
    args = parser.parse_args(argv)

    now = parse_time(args.now) if args.now else datetime.now(timezone.utc)
    report = load_report(now, portfolio_path=args.portfolio)

    changed: set[str] | None = None
    if args.changed_paths is not None:
        changed = {p.strip() for p in args.changed_paths.split(",") if p.strip()}

    try:
        blocking, reason = resolve_blocking(
            fail_on_stale=args.fail_on_stale,
            fail_when_inventory_changed=args.fail_on_stale_when_inventory_changed,
            diff_base=args.diff_base,
            diff_head=args.diff_head,
            changed_paths=changed,
            repo=args.repo,
        )
    except (ValueError, RuntimeError) as exc:
        print(f"FAIL: freshness gate could not resolve blocking mode: {exc}", file=sys.stderr)
        return 2

    report["blocking"] = blocking
    report["blocking_reason"] = reason

    output = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.json_out:
        args.json_out.write_text(output, encoding="utf-8")
    print(render_markdown(report), end="")
    print(f"Freshness gate mode: {'BLOCKING' if blocking else 'INFORMATIONAL'} ({reason})")
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if args.github_summary and summary_path:
        with open(summary_path, "a", encoding="utf-8") as handle:
            handle.write(render_markdown(report))
            handle.write(
                f"\nFreshness gate mode: "
                f"{'BLOCKING' if blocking else 'INFORMATIONAL'} ({reason})\n"
            )

    if blocking and report["any_stale"]:
        print("FAIL: portfolio inventory/evidence is stale", file=sys.stderr)
        return 1
    if report["any_stale"] and not blocking:
        print(
            "WARN: portfolio inventory/evidence is stale "
            "(informational; inventory ownership paths unchanged)",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
