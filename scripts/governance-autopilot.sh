#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat >&2 <<'EOF'
usage: governance-autopilot.sh --policy FILE --inventory FILE --output FILE
       [--apply-safe-cleanup]

The default mode is read-only. Safe cleanup is only eligible for files below
the policy-owned runtime root when its ownership marker exists. Approval items
are reported; they are never applied by this command.
EOF
  exit 2
}

policy=''
inventory=''
output=''
apply_safe_cleanup=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --policy) policy=${2:?missing value for --policy}; shift 2 ;;
    --inventory) inventory=${2:?missing value for --inventory}; shift 2 ;;
    --output) output=${2:?missing value for --output}; shift 2 ;;
    --apply-safe-cleanup) apply_safe_cleanup=1; shift ;;
    -h|--help) usage ;;
    *) echo "unknown argument: $1" >&2; usage ;;
  esac
done

[[ -n "$policy" && -n "$inventory" && -n "$output" ]] || usage
[[ -f "$policy" ]] || { echo "policy not found: $policy" >&2; exit 1; }
[[ -f "$inventory" ]] || { echo "inventory not found: $inventory" >&2; exit 1; }

exec python3 - "$policy" "$inventory" "$output" "$apply_safe_cleanup" <<'PY'
from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import shutil
import subprocess
import sys

import yaml


policy_path = Path(sys.argv[1]).resolve()
inventory_path = Path(sys.argv[2]).resolve()
output_path = Path(sys.argv[3]).resolve()
apply_safe_cleanup = sys.argv[4] == "1"


def load_policy(path: Path) -> dict:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("schema_version") != 1:
        raise SystemExit(f"invalid autonomy policy: {path}")
    for key in ("automatic_actions", "approval_required_actions", "never_automatic_actions", "exception_defaults"):
        if not isinstance(value.get(key), (list, dict)):
            raise SystemExit(f"invalid policy field: {key}")
    return value


def exception(policy: dict, candidate: str, reason: str, risk: str = "high") -> dict:
    defaults = policy["exception_defaults"]
    return {
        "candidate": candidate,
        "classification": "approval_required",
        "risk": risk,
        "reason": reason,
        "owner": defaults["owner"],
        "recovery": defaults["recovery"],
        "next_step": defaults["next_step"],
        "allowed_automatic_actions": ["observe", "report", "recheck"],
    }


def read_inventory(path: Path, policy: dict) -> tuple[list[dict], list[dict], dict]:
    rows: list[dict] = []
    approvals: list[dict] = []
    malformed = 0
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle, delimiter="\t")
        try:
            header = next(reader)
        except StopIteration:
            raise SystemExit("inventory is empty")
        if not header or len(set(header)) != len(header):
            raise SystemExit("inventory header is empty or has duplicate fields")
        indexes = {name: index for index, name in enumerate(header)}
        if "candidate" not in indexes:
            raise SystemExit("inventory must contain a candidate field")

        for line_number, values in enumerate(reader, start=2):
            if len(values) != len(header):
                malformed += 1
                approvals.append(exception(policy, f"line:{line_number}", "malformed inventory row width"))
                continue
            row = {name: values[index] for name, index in indexes.items()}
            candidate = row.get("candidate", "") or row.get("path", "") or f"line:{line_number}"
            row["candidate"] = candidate
            status = row.get("status", "").strip().lower()
            role = row.get("role", "").strip().lower()
            if status in {"dirty", "unreadable"}:
                approvals.append(exception(policy, candidate, f"inventory status is {status}"))
                row["classification"] = "approval_required"
            elif role == "unresolved" or not row.get("git_top", "").strip():
                approvals.append(exception(policy, candidate, "Git root identity is unresolved"))
                row["classification"] = "approval_required"
            elif not status:
                approvals.append(exception(policy, candidate, "inventory status is missing"))
                row["classification"] = "approval_required"
            else:
                row["classification"] = "automatic_observation"
            rows.append(row)

    summary = {
        "total_rows": len(rows) + malformed,
        "clean_rows": sum(row.get("classification") == "automatic_observation" for row in rows),
        "approval_required_rows": len(approvals),
        "malformed_rows": malformed,
    }
    return rows, approvals, summary


def safe_cleanup_plan(policy: dict) -> tuple[dict, list[dict]]:
    config = policy.get("safe_cleanup", {})
    if not config.get("enabled", False):
        return {"enabled": False, "status": "disabled", "candidates": []}, []
    root = Path(str(config.get("root", ""))).expanduser()
    if not root.is_absolute() or root in {Path("/"), Path.home(), Path("/home/jerry/workspace")}:
        return {"enabled": True, "root": str(root), "status": "blocked_unsafe_root", "candidates": [], "applied": []}, []
    marker = root / str(config.get("ownership_marker", ""))
    result = {"enabled": True, "root": str(root), "status": "blocked", "candidates": [], "applied": []}
    if not root.is_dir():
        result["status"] = "not_present"
        return result, []
    if not marker.is_file():
        result["status"] = "ownership_marker_missing"
        return result, []

    patterns = [str(pattern) for pattern in config.get("patterns", [])]
    candidates = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.is_symlink() or path == marker:
            continue
        if any(path.match(pattern) for pattern in patterns):
            candidates.append(path)
    result["candidates"] = [str(path) for path in candidates]
    result["status"] = "planned" if candidates else "clean"
    if not apply_safe_cleanup:
        return result, []

    gio = shutil.which("gio")
    if gio is None:
        result["status"] = "blocked_gio_missing"
        return result, []
    for path in candidates:
        subprocess.run([gio, "trash", "--", str(path)], check=True)
        result["applied"].append(str(path))
    result["status"] = "applied" if result["applied"] else "clean"
    return result, result["applied"]


policy = load_policy(policy_path)
rows, approvals, summary = read_inventory(inventory_path, policy)
cleanup, _ = safe_cleanup_plan(policy)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


report = {
    "schema_version": 1,
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "policy": str(policy_path),
    "policy_sha256": sha256(policy_path),
    "source_inventory": str(inventory_path),
    "source_inventory_sha256": sha256(inventory_path),
    "operating_model": policy.get("operating_model"),
    "automatic_actions": policy["automatic_actions"],
    "approval_required_actions": policy["approval_required_actions"],
    "never_automatic_actions": policy["never_automatic_actions"],
    "summary": summary,
    "automatic_observations": rows,
    "approval_queue": approvals,
    "safe_cleanup": cleanup,
}
output_path.parent.mkdir(parents=True, exist_ok=True)
output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(f"PASS: governance autopilot report written to {output_path}")
print(json.dumps({"summary": summary, "approval_queue": len(approvals), "safe_cleanup": cleanup["status"]}, ensure_ascii=False, sort_keys=True))
PY
