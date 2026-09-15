"""Harness: attempt lifecycle, worker adapters, result ingest.

Fake and production workers share worker_contract.WorkerResult.
Only DurableGraphRuntime commits transitions.
"""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, Protocol

from .durable_models import Attempt, Run
from .durable_runtime import DurableApplyResult, DurableGraphRuntime
from .models import Event
from .worker_contract import (
    ProposedOutcome,
    WorkerResult,
    WorkerResultError,
    read_worker_result,
    validate_worker_result,
    write_worker_result,
)

RESULT_REL_PATH = ".agent-session/result.json"
CONTEXT_REL_PATH = ".agent-session/worker-context.json"
BINDING_REL_PATH = ".agent-session/graph-binding.json"


def _utcnow() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex}"


class WorkerAdapter(Protocol):
    worker_type: str

    def execute(self, *, run: Run, attempt: Attempt, context: dict[str, Any]) -> WorkerResult:
        ...


@dataclass
class IngestResult:
    apply: DurableApplyResult
    attempt: Attempt
    duplicate_ingest: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "duplicate_ingest": self.duplicate_ingest,
            "attempt": self.attempt.to_dict(),
            "apply": self.apply.to_dict(),
        }


class FakeWorkerAdapter:
    """Deterministic fixture worker for CI / crash-resume tests."""

    worker_type = "fake"

    def __init__(self, *, head_sha: str = "b" * 40, actor_suffix: str = "1") -> None:
        self.head_sha = head_sha
        self.actor_suffix = actor_suffix

    def execute(self, *, run: Run, attempt: Attempt, context: dict[str, Any]) -> WorkerResult:
        node = attempt.node
        repo = context.get("repository", f"jerry200176-png/{run.project}")
        base = run.base_sha or run.head_sha or self.head_sha

        def outcome(
            outcome_type: str,
            actor_role: str,
            actor_id: str,
            *,
            head: Optional[str] = None,
            conclusion: str = "ok",
            evidence: Optional[dict[str, Any]] = None,
        ) -> WorkerResult:
            po = ProposedOutcome(
                outcome_type=outcome_type,
                actor_id=actor_id,
                actor_role=actor_role,
                head_sha=head if head is not None else (run.head_sha or base),
                base_sha=base,
                conclusion=conclusion,
                evidence=evidence or {"source": "fake_worker"},
                repository=repo,
            )
            return WorkerResult(
                status="success",
                summary=f"fake completed {outcome_type} at node={node}",
                idempotency_key=f"{attempt.attempt_id}:{outcome_type}",
                artifacts=({"kind": "note", "uri": f"fake://{attempt.attempt_id}"},),
                evidence=({"kind": "fixture", "ref": attempt.attempt_id, "summary": "fake"},),
                proposed_outcome=po,
            )

        if node == "investigator":
            return outcome("INVESTIGATION_COMPLETED", "investigator", f"inv-{self.actor_suffix}")
        if node == "builder":
            return outcome(
                "BUILD_COMPLETED",
                "builder",
                f"builder-{self.actor_suffix}",
                head=self.head_sha,
            )
        if node == "reviewer":
            # Distinct reviewer actor from builder by default.
            return outcome(
                "REVIEW_APPROVED",
                "reviewer",
                f"reviewer-{self.actor_suffix}",
                head=run.head_sha or self.head_sha,
                conclusion="ok",
            )
        if node == "human_gate":
            return outcome(
                "HUMAN_APPROVED",
                "human",
                "founder-stub",
                head=run.head_sha or self.head_sha,
                conclusion="approved",
            )
        if node == "intake":
            # Intake is system-owned; fake worker should not normally run here.
            raise WorkerResultError("intake is system-owned; refuse fake worker execute")
        raise WorkerResultError(f"fake worker has no fixture for node={node}")


class FileWorkerAdapter:
    """Production-shaped adapter: read `.agent-session/result.json` written by an external worker."""

    worker_type = "file"

    def __init__(self, worktree: str | Path) -> None:
        self.worktree = Path(worktree)

    def execute(self, *, run: Run, attempt: Attempt, context: dict[str, Any]) -> WorkerResult:
        path = self.worktree / RESULT_REL_PATH
        if not path.is_file():
            raise WorkerResultError(f"missing worker result file: {path}")
        return read_worker_result(path)


def write_worker_context(
    worktree: str | Path,
    *,
    run: Run,
    attempt: Attempt,
    goal_objective: Optional[str] = None,
    extra: Optional[dict[str, Any]] = None,
) -> Path:
    """Write launch context for a replaceable worker. Not canonical state."""
    worktree = Path(worktree)
    payload = {
        "RUN_ID": run.run_id,
        "ATTEMPT_ID": attempt.attempt_id,
        "NODE": attempt.node,
        "PROJECT": run.project,
        "WORKTREE": str(worktree),
        "GRAPH_VERSION": run.graph_version,
        "GOAL_OBJECTIVE": goal_objective,
        "BASE_SHA": run.base_sha,
        "HEAD_SHA": run.head_sha,
        "result_path": str(worktree / RESULT_REL_PATH),
    }
    if extra:
        payload.update(extra)
    path = worktree / CONTEXT_REL_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    binding = {
        "run_id": run.run_id,
        "attempt_id": attempt.attempt_id,
        "node": attempt.node,
        "project": run.project,
        "worktree": str(worktree),
    }
    (worktree / BINDING_REL_PATH).write_text(
        json.dumps(binding, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    _mirror_manifest_fields(worktree, binding)
    return path


def worker_env(run: Run, attempt: Attempt, worktree: str | Path) -> dict[str, str]:
    return {
        "RUN_ID": run.run_id,
        "ATTEMPT_ID": attempt.attempt_id,
        "NODE": attempt.node,
        "PROJECT": run.project,
        "WORKTREE": str(worktree),
        "GRAPH_CONTROL_PLANE": "1",
    }


def _mirror_manifest_fields(worktree: Path, binding: dict[str, Any]) -> None:
    """Best-effort mirror into session manifest without rewriting agent-start."""
    manifest_path = worktree / ".agent-session" / "manifest.json"
    if not manifest_path.is_file():
        return
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return
    data["run_id"] = binding["run_id"]
    data["attempt_id"] = binding["attempt_id"]
    data["node"] = binding["node"]
    manifest_path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


class GraphHarness:
    def __init__(self, runtime: DurableGraphRuntime) -> None:
        self.runtime = runtime

    def ingest_worker_result(
        self,
        *,
        run_id: str,
        attempt_id: str,
        result: WorkerResult | dict[str, Any],
        mark_tested_sha: Optional[str] = None,
    ) -> IngestResult:
        if isinstance(result, dict):
            result = validate_worker_result(result)
        attempt = self.runtime.store.get_attempt(attempt_id)
        if attempt is None:
            raise KeyError(f"unknown attempt_id: {attempt_id}")
        if attempt.run_id != run_id:
            raise ValueError("attempt_id does not belong to run_id")

        ingest_key = result.idempotency_key
        existing_attempt = self.runtime.store.get_attempt_by_ingest_key(ingest_key)
        if existing_attempt is not None:
            # Same attempt completed earlier — idempotent success.
            run = self.runtime.get_run(run_id)
            events = self.runtime.list_events(run_id)
            last = events[-1] if events else None
            return IngestResult(
                apply=DurableApplyResult(
                    accepted=True,
                    duplicate=True,
                    run=run,
                    event=last,
                    reason="duplicate result ingest (idempotent)",
                ),
                attempt=existing_attempt,
                duplicate_ingest=True,
            )

        if attempt.status not in ("started", "failed"):
            # Already finished without ingest key match → safe reject
            raise WorkerResultError(
                f"attempt {attempt_id} is not ingestible (status={attempt.status})"
            )

        if result.status != "success" or result.proposed_outcome is None:
            now = _utcnow()
            attempt.status = "failed"
            attempt.ended_at = now
            attempt.result_ingest_key = ingest_key
            with self.runtime.store.transaction() as conn:
                self.runtime.store.update_attempt(attempt, conn=conn)
            run = self.runtime.get_run(run_id)
            return IngestResult(
                apply=DurableApplyResult(
                    accepted=False,
                    duplicate=False,
                    run=run,
                    reason=f"worker status={result.status}; no transition committed",
                ),
                attempt=attempt,
            )

        po = result.proposed_outcome
        # Fail closed: proposed event node must match attempt node (except NODE_FAILED).
        expected_node = {
            "INVESTIGATION_COMPLETED": "investigator",
            "BUILD_COMPLETED": "builder",
            "REVIEW_REJECTED": "reviewer",
            "REVIEW_APPROVED": "reviewer",
            "HUMAN_APPROVED": "human_gate",
            "HUMAN_REJECTED": "human_gate",
            "NODE_FAILED": attempt.node,
        }[po.outcome_type]
        if expected_node != attempt.node and po.outcome_type != "NODE_FAILED":
            raise WorkerResultError(
                f"proposed outcome {po.outcome_type} does not match attempt node {attempt.node}"
            )

        evidence_refs = tuple(f"{e['kind']}:{e['ref']}" for e in result.evidence)
        event_id = f"{attempt_id}:{po.outcome_type}"
        graph_event = Event(
            event_id=event_id,
            task_id=run_id,
            timestamp=_utcnow(),
            event_type=po.outcome_type,
            node=attempt.node if po.outcome_type == "NODE_FAILED" else expected_node,
            actor_id=po.actor_id,
            actor_role=po.actor_role,
            repository=po.repository or f"jerry200176-png/{self.runtime.get_run(run_id).project}",
            base_sha=po.base_sha or self.runtime.get_run(run_id).base_sha,
            head_sha=po.head_sha,
            conclusion=po.conclusion,
            evidence=po.evidence or {"summary": result.summary},
        )

        # Single transaction: artifacts + event + projection + attempt completion
        store = self.runtime.store
        with store.transaction() as conn:
            # Re-check ingest key inside transaction
            if store.get_attempt_by_ingest_key(ingest_key) is not None:
                run = store.get_run(run_id)
                assert run is not None
                att = store.get_attempt_by_ingest_key(ingest_key)
                assert att is not None
                return IngestResult(
                    apply=DurableApplyResult(
                        accepted=True,
                        duplicate=True,
                        run=run,
                        reason="duplicate result ingest (idempotent)",
                    ),
                    attempt=att,
                    duplicate_ingest=True,
                )

            apply = self.runtime._apply_in_tx(
                conn,
                run_id=run_id,
                canonical=self.runtime._graph_event_to_canonical(
                    graph_event, attempt_id=attempt_id, evidence_refs=evidence_refs
                ),
                ingest_key=ingest_key,
            )

            now = _utcnow()
            attempt.result_ingest_key = ingest_key
            attempt.ended_at = now
            if apply.accepted:
                attempt.status = "ingested"
            else:
                attempt.status = "rejected"
            store.update_attempt(attempt, conn=conn)

            for art in result.artifacts:
                store.insert_artifact(
                    artifact_id=_new_id("art"),
                    run_id=run_id,
                    attempt_id=attempt_id,
                    kind=str(art["kind"]),
                    uri=str(art["uri"]),
                    sha256=art.get("sha256"),
                    created_at=now,
                    conn=conn,
                )

            if apply.accepted and mark_tested_sha:
                run = apply.run
                expected = run.state_version
                run.tested_sha = mark_tested_sha
                run.updated_at = now
                store.update_run_projection(run, expected_version=expected, conn=conn)
                apply.run = run

        return IngestResult(apply=apply, attempt=attempt, duplicate_ingest=apply.duplicate)

    def step(
        self,
        run_id: str,
        *,
        worker: Optional[WorkerAdapter] = None,
        model_profile: Optional[str] = None,
        worker_pid: Optional[int] = None,
        write_context: bool = True,
    ) -> IngestResult:
        run = self.runtime.get_run(run_id)
        worker = worker or FakeWorkerAdapter(
            head_sha=run.head_sha or run.base_sha or ("c" * 40)
        )
        attempt = self.runtime.start_attempt(
            run_id,
            worker_type=getattr(worker, "worker_type", "unknown"),
            model_profile=model_profile,
            worker_pid=worker_pid if worker_pid is not None else os.getpid(),
        )
        worktree = run.worktree or os.getcwd()
        context = {
            "repository": f"jerry200176-png/{run.project}",
            "RUN_ID": run.run_id,
            "ATTEMPT_ID": attempt.attempt_id,
            "NODE": attempt.node,
            "PROJECT": run.project,
            "WORKTREE": worktree,
        }
        if write_context and run.worktree:
            goal = self.runtime.store.get_goal(run.goal_id)
            write_worker_context(
                run.worktree,
                run=run,
                attempt=attempt,
                goal_objective=goal.objective if goal else None,
            )
            # Optionally persist a result file for file-worker parity when fake runs.
            if isinstance(worker, FakeWorkerAdapter):
                result = worker.execute(run=run, attempt=attempt, context=context)
                write_worker_result(Path(run.worktree) / RESULT_REL_PATH, result)
            else:
                result = worker.execute(run=run, attempt=attempt, context=context)
        else:
            result = worker.execute(run=run, attempt=attempt, context=context)

        mark = None
        if result.proposed_outcome and result.proposed_outcome.outcome_type == "BUILD_COMPLETED":
            mark = result.proposed_outcome.head_sha
        return self.ingest_worker_result(
            run_id=run_id,
            attempt_id=attempt.attempt_id,
            result=result,
            mark_tested_sha=mark,
        )
