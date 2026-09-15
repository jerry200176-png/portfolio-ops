"""Bounded single-tick scheduler (no daemon).

Advances one runnable Run by one legal step: worker node → step, or
approved_for_effect → reconcile only. Does not invent policy.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from .durable_runtime import DurableGraphRuntime
from .harness import FakeWorkerAdapter, GraphHarness
from .reconciler import GraphReconciler


@dataclass
class ScheduleTickResult:
    examined: int
    advanced: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return {"examined": self.examined, "advanced": self.advanced}


class GraphScheduler:
    def __init__(
        self,
        runtime: DurableGraphRuntime,
        *,
        reconciler: Optional[GraphReconciler] = None,
        head_sha: str = "c" * 40,
    ) -> None:
        self.runtime = runtime
        self.reconciler = reconciler
        self.head_sha = head_sha
        self.harness = GraphHarness(runtime)

    def list_runnable(self, limit: int = 20) -> list[str]:
        # Minimal: scan recent runs table.
        rows = self.runtime.store._conn.execute(
            """
            SELECT run_id FROM runs
            WHERE closed=0 AND stopped=0
              AND status IN ('running','waiting_worker','waiting_for_approval','approved_for_effect')
            ORDER BY updated_at ASC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [r["run_id"] for r in rows]

    def tick(self, *, limit: int = 5, pr_number: Optional[int] = None) -> ScheduleTickResult:
        advanced = []
        ids = self.list_runnable(limit=limit)
        for run_id in ids:
            run = self.runtime.get_run(run_id)
            if run.status == "waiting_for_approval":
                advanced.append({"run_id": run_id, "action": "skip_waiting_for_approval"})
                continue
            if run.current_node == "approved_for_effect":
                if self.reconciler is None:
                    advanced.append({"run_id": run_id, "action": "skip_no_reconciler"})
                    continue
                out = self.reconciler.reconcile_run(run_id, pr_number=pr_number)
                advanced.append({"run_id": run_id, "action": "reconcile", "result": out.to_dict()})
                continue
            if run.current_node in ("investigator", "builder", "reviewer"):
                try:
                    stepped = self.harness.step(
                        run_id,
                        worker=FakeWorkerAdapter(head_sha=run.head_sha or self.head_sha),
                        write_context=False,
                    )
                    advanced.append(
                        {
                            "run_id": run_id,
                            "action": "step",
                            "accepted": stepped.apply.accepted,
                            "node": stepped.apply.run.current_node,
                        }
                    )
                except Exception as exc:  # noqa: BLE001 — tick must continue
                    advanced.append({"run_id": run_id, "action": "step_error", "error": str(exc)})
                continue
            advanced.append({"run_id": run_id, "action": "noop", "node": run.current_node})
        return ScheduleTickResult(examined=len(ids), advanced=advanced)
