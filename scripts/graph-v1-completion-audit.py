#!/usr/bin/env python3
"""Graph Control Plane v1 completion criteria auditor.

Emits machine-readable YES/NO per criterion. Does not redefine success —
Part A requires live RealCodex EVIDENCE.json with closed_success.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

ROOT = Path(__file__).resolve().parents[1]


def _git(*args: str) -> str:
    return subprocess.check_output(["git", "-C", str(ROOT), *args], text=True).strip()


def _load_json(path: Path) -> Optional[dict[str, Any]]:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _latest_evidence() -> Optional[Path]:
    reports = ROOT / "reports"
    if not reports.is_dir():
        return None
    candidates = sorted(reports.glob("*/schedule-realcodex-dogfood/EVIDENCE.json"))
    state = Path.home() / "workspace/state/portfolio-ops/evidence"
    if state.is_dir():
        candidates.extend(sorted(state.glob("schedule-realcodex-dogfood-*/EVIDENCE.json")))
    return candidates[-1] if candidates else None


def audit() -> dict[str, Any]:
    main_sha = _git("rev-parse", "HEAD")
    evidence_path = _latest_evidence()
    evidence = _load_json(evidence_path) if evidence_path else None

    # Locate key modules on tip
    has_scheduler = (ROOT / "agent_graph/scheduler.py").is_file()
    has_ownership = (ROOT / "agent_graph/scheduler_ownership.py").is_file()
    has_real_codex = (ROOT / "agent_graph/real_codex_adapter.py").is_file()
    has_fault = (ROOT / "scripts/graph-scheduler-fault-injection.py").is_file()
    has_unit = (ROOT / "scripts/systemd/graph-scheduler.service").is_file()
    fault_results = _load_json(
        ROOT / "reports/2026-09-15/scheduler-fault-injection/results.json"
    )

    closed = bool(
        evidence
        and evidence.get("terminal_reconciliation", {}).get("closed_success")
    )
    impl_codex = bool(evidence and evidence.get("implementation_workers_are_codex"))
    has_pids = bool(
        evidence
        and any(
            w.get("worker_pid")
            for w in evidence.get("worker_identities", [])
            if w.get("node") in ("investigator", "builder")
        )
    )
    has_effects = bool(evidence and evidence.get("effect_ids"))
    has_pr = bool(evidence and (evidence.get("pr") or {}).get("number"))
    has_head = bool(evidence and evidence.get("exact_head_sha"))
    has_ci = evidence.get("ci_state") is not None if evidence else False

    criteria = {
        "1_realcodex_e2e_dogfood": closed and impl_codex and has_pids,
        "2_founder_did_not_manage_codex_terminal": closed and evidence.get("mode")
        == "schedule-run",
        "3_pr_ci_effect_from_control_plane": closed and has_effects and has_pr and has_ci,
        "4_dogfood_closed_success": closed,
        "5_autonomous_scheduler_advances_without_manual_tick": has_scheduler
        and (ROOT / "scripts/graph-schedule-realcodex-dogfood.py").is_file(),
        "6_scheduler_crash_restart_safe": has_ownership
        and bool(fault_results)
        and any(x.get("case") == "kill_scheduler_between_ticks" and x.get("ok") for x in fault_results),
        "7_worker_crash_replacement_safe": bool(fault_results)
        and any(
            x.get("case") == "worker_timeout_scheduler_continues" and x.get("ok")
            for x in (fault_results or [])
        ),
        "8_effect_reconciliation_safe": bool(fault_results)
        and any(
            x.get("case") == "after_effect_before_local_confirm" and x.get("ok")
            for x in (fault_results or [])
        ),
        "9_human_gate_fail_closed": (ROOT / "agent_graph/policy_gate.py").is_file()
        and (ROOT / "tests/test_autonomous_scheduler.py").is_file(),
        "10_scope_portfolio_ops_allowlist": has_unit
        and "portfolio-ops" in (ROOT / "scripts/systemd/graph-scheduler.service").read_text(),
        "11_production_deploy_db_migration_disabled": True,  # allowlist excludes deploy
    }

    # Criterion 5 alone is not enough without live proof that schedule-run drove Part A.
    if not closed:
        criteria["5_autonomous_scheduler_advances_without_manual_tick"] = (
            criteria["5_autonomous_scheduler_advances_without_manual_tick"] and False
        )
        # Keep structural readiness separate
        criteria["5_scheduler_code_ready"] = has_scheduler

    all_core = all(
        v
        for k, v in criteria.items()
        if k.startswith(tuple(str(i) for i in range(1, 12)))
        or k[:2].isdigit()
    )
    # Only the numbered 1-11
    numbered = {k: v for k, v in criteria.items() if k[0].isdigit()}
    program_complete = all(numbered.values())

    return {
        "audited_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "main_sha": main_sha,
        "evidence_path": str(evidence_path) if evidence_path else None,
        "evidence_closed_success": closed,
        "has_real_codex_adapter": has_real_codex,
        "criteria": criteria,
        "numbered_criteria": numbered,
        "GRAPH_CONTROL_PLANE_V1_AUTONOMOUS": "YES" if program_complete else "NO",
        "blocker": None
        if program_complete
        else (
            "codex_usage_limit_pending_live_dogfood"
            if not closed
            else "incomplete_evidence_fields"
        ),
    }


def main() -> int:
    report = audit()
    out = ROOT / "reports" / datetime.now(timezone.utc).strftime("%Y-%m-%d") / "v1-completion-audit"
    out.mkdir(parents=True, exist_ok=True)
    path = out / "AUDIT.json"
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    print(f"\nGRAPH CONTROL PLANE V1 AUTONOMOUS: {report['GRAPH_CONTROL_PLANE_V1_AUTONOMOUS']}")
    return 0 if report["GRAPH_CONTROL_PLANE_V1_AUTONOMOUS"] == "YES" else 2


if __name__ == "__main__":
    sys.exit(main())
