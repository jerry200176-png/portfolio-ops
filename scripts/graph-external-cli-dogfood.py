#!/usr/bin/env python3
"""Dogfood: external_cli stub handoff against a disposable control-plane DB.

Writes evidence under reports/YYYY-MM-DD/external-cli-handoff/.
Does not enable graph-scheduler or touch production DBs.
"""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from agent_graph.durable_runtime import DurableGraphRuntime
from agent_graph.external_cli_adapter import ExternalCliWorkerAdapter, build_stub_command
from agent_graph.harness import GraphHarness
from agent_graph.sqlite_store import SqliteControlPlaneStore

ROOT = Path(__file__).resolve().parent.parent
STUB = ROOT / "scripts" / "graph-external-cli-stub-worker.py"


def _utcnow() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def main() -> int:
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    out_dir = ROOT / "reports" / day / "external-cli-handoff"
    out_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="ext-cli-dogfood-") as tmp:
        root = Path(tmp)
        db = root / "control-plane" / "graph.sqlite"
        db.parent.mkdir(parents=True)
        worktree = root / "task-wt"
        worktree.mkdir()
        (worktree / ".git").mkdir()

        store = SqliteControlPlaneStore(str(db))
        rt = DurableGraphRuntime(store)
        harness = GraphHarness(rt)
        run = rt.create_run(
            objective="dogfood external_cli independent process handoff",
            project="portfolio-ops",
            base_sha="a" * 40,
            worktree=str(worktree),
            branch="chore/task-external-cli-dogfood",
        )
        worker = ExternalCliWorkerAdapter(
            provider_id="stub",
            command_builder=lambda wt, prompt, ctx: build_stub_command(
                wt, prompt, {**ctx, "stub_bin": str(STUB)}
            ),
            timeout_sec=30.0,
            canonical_db_path=db,
        )
        step = harness.step(
            run.run_id,
            worker=worker,
            model_profile="external_cli:stub",
            extra_context={"CANONICAL_DB_PATH": str(db)},
        )
        after = rt.get_run(run.run_id)
        evidence = {
            "completed_at": _utcnow(),
            "ok": bool(step.apply.accepted),
            "run_id": run.run_id,
            "attempt": step.attempt.to_dict(),
            "apply": step.apply.to_dict(),
            "launch": worker.last_launch.to_dict() if worker.last_launch else None,
            "current_node_after": after.current_node,
            "state_version_after": after.state_version,
            "host_pid": os.getpid(),
            "worker_pid": worker.last_launch.pid if worker.last_launch else None,
            "independent_process": bool(
                worker.last_launch and worker.last_launch.pid and worker.last_launch.pid != os.getpid()
            ),
            "worker_type_domain": "external_cli",
            "provider_id_observational": "stub",
            "chat_dependence": False,
        }
        path = out_dir / "summary.json"
        path.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({"evidence": str(path), **evidence}, indent=2, sort_keys=True))
        rt.close()
        return 0 if evidence["ok"] and evidence["independent_process"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
