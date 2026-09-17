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

from .canonical_paths import (
    CanonicalPathError,
    assert_canonical_db_outside_worktree,
    run_node_resource_key,
    safe_result_path,
    worktree_resource_key,
)
from .durable_models import Attempt, Run
from .durable_runtime import DurableApplyResult, DurableGraphRuntime
from .models import Event
from .sqlite_store import (
    LeaseBusyError,
    PreviousWorkerStillAliveError,
    PreviousWorkerUnverifiableError,
    StaleLeaseError,
)
from .worker_contract import (
    BINDING_REL_PATH,
    CONTEXT_REL_PATH,
    RESULT_REL_PATH,
    ProposedOutcome,
    WorkerResult,
    WorkerResultError,
    read_worker_result,
    validate_worker_result,
    write_worker_result,
)

# Re-export path constants for existing imports.
__all__ = [
    "BINDING_REL_PATH",
    "CONTEXT_REL_PATH",
    "RESULT_REL_PATH",
    "FakeWorkerAdapter",
    "FileWorkerAdapter",
    "GraphHarness",
    "IngestResult",
    "WorkerAdapter",
    "write_worker_context",
    "worker_env",
]

DEFAULT_LEASE_TTL_SEC = 3600


def _utcnow() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex}"


def _iso_plus_seconds(base_iso: str, seconds: float) -> str:
    dt = datetime.fromisoformat(base_iso.replace("Z", "+00:00"))
    return (
        (dt + __import__("datetime").timedelta(seconds=seconds))
        .astimezone(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _check_result_identity_consistency(
    *,
    result: WorkerResult,
    run_id: str,
    attempt_id: str,
    node: str,
    expected_state_version: int,
) -> None:
    """Worker payload may echo identity fields; mismatches fail closed.

    Authority remains the canonical Attempt row — never the worker file.
    """
    raw = result.raw or {}
    checks = {
        "run_id": run_id,
        "attempt_id": attempt_id,
        "node": node,
        "expected_state_version": expected_state_version,
        "RUN_ID": run_id,
        "ATTEMPT_ID": attempt_id,
        "NODE": node,
        "EXPECTED_STATE_VERSION": expected_state_version,
    }
    for key, expected in checks.items():
        if key not in raw or raw[key] is None:
            continue
        if str(raw[key]) != str(expected):
            raise WorkerResultError(
                f"worker result identity mismatch on {key}: "
                f"got {raw[key]!r} expected {expected!r}"
            )



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
            raise WorkerResultError(
                "human_gate requires control-plane Founder Approval "
                "(graph approve); workers cannot approve"
            )
        if node == "approved_for_effect":
            raise WorkerResultError("approved_for_effect is terminal for Phase 1C; no worker step")
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
        path = safe_result_path(self.worktree)
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
        "EXPECTED_STATE_VERSION": attempt.expected_state_version,
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
        "expected_state_version": attempt.expected_state_version,
        "project": run.project,
        "worktree": str(worktree),
    }
    (worktree / BINDING_REL_PATH).write_text(
        json.dumps(binding, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return path


def worker_env(run: Run, attempt: Attempt, worktree: str | Path) -> dict[str, str]:
    return {
        "RUN_ID": run.run_id,
        "ATTEMPT_ID": attempt.attempt_id,
        "NODE": attempt.node,
        "PROJECT": run.project,
        "WORKTREE": str(worktree),
        "EXPECTED_STATE_VERSION": str(attempt.expected_state_version),
        "GRAPH_CONTROL_PLANE": "1",
    }


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
        # Worker ingest always uses the version bound at attempt dispatch.
        # There is no unsafe bypass for normal worker adapters.
        if attempt.expected_state_version is None:
            raise WorkerResultError(
                f"attempt {attempt_id} missing expected_state_version binding"
            )
        expected_state_version = int(attempt.expected_state_version)

        # Controller-owned identity: payload echoes are consistency-only.
        _check_result_identity_consistency(
            result=result,
            run_id=run_id,
            attempt_id=attempt_id,
            node=attempt.node,
            expected_state_version=expected_state_version,
        )

        # Fencing before status: reclaimed/orphaned Attempts fail closed here.
        current = self.runtime.get_run(run_id)
        if int(attempt.fencing_token) > 0 and current.worktree:
            now = _utcnow()
            resource = worktree_resource_key(current.worktree)
            try:
                self.runtime.store.assert_lease_fence(
                    resource_key=resource,
                    attempt_id=attempt.attempt_id,
                    fencing_token=int(attempt.fencing_token),
                    now=now,
                )
            except StaleLeaseError as exc:
                if attempt.status in ("started", "failed"):
                    attempt.status = "rejected"
                    attempt.ended_at = now
                    with self.runtime.store.transaction() as conn:
                        self.runtime.store.update_attempt(attempt, conn=conn)
                return IngestResult(
                    apply=DurableApplyResult(
                        accepted=False,
                        duplicate=False,
                        run=current,
                        reason=str(exc),
                        blocker="stale_execution_lease",
                    ),
                    attempt=attempt,
                )

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

        # Fail closed before any transition if Run moved under this attempt.
        if current.state_version != expected_state_version:
            now = _utcnow()
            attempt.status = "rejected"
            attempt.ended_at = now
            with self.runtime.store.transaction() as conn:
                self.runtime.store.update_attempt(attempt, conn=conn)
            return IngestResult(
                apply=DurableApplyResult(
                    accepted=False,
                    duplicate=False,
                    run=current,
                    reason=(
                        f"stale state_version: expected {expected_state_version} "
                        f"got {current.state_version}"
                    ),
                    blocker="stale_state_version",
                ),
                attempt=attempt,
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
        # Workers must never forge Founder Approval transitions.
        if po.outcome_type in ("HUMAN_APPROVED", "HUMAN_REJECTED"):
            raise WorkerResultError(
                f"worker must not propose {po.outcome_type}; "
                "use control-plane graph approve path"
            )
        # Fail closed: proposed event node must match attempt node (except NODE_FAILED).
        expected_node = {
            "INVESTIGATION_COMPLETED": "investigator",
            "BUILD_COMPLETED": "builder",
            "REVIEW_REJECTED": "reviewer",
            "REVIEW_APPROVED": "reviewer",
            "NODE_FAILED": attempt.node,
        }.get(po.outcome_type)
        if expected_node is None:
            raise WorkerResultError(f"unsupported worker outcome_type: {po.outcome_type}")
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
                expected_state_version=expected_state_version,
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
        extra_context: Optional[dict[str, Any]] = None,
        lease_ttl_sec: float = DEFAULT_LEASE_TTL_SEC,
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
        goal = self.runtime.store.get_goal(run.goal_id)
        context: dict[str, Any] = {
            "repository": f"jerry200176-png/{run.project}",
            "RUN_ID": run.run_id,
            "ATTEMPT_ID": attempt.attempt_id,
            "NODE": attempt.node,
            "PROJECT": run.project,
            "WORKTREE": worktree,
            "GOAL_OBJECTIVE": goal.objective if goal else None,
            "SUCCESS_CONDITION": goal.success_condition if goal else None,
            "EXPECTED_STATE_VERSION": attempt.expected_state_version,
        }
        if extra_context:
            context.update(extra_context)

        # Real external CLI workers (Codex / external_cli) require execution leases
        # + DB outside worktree. Domain worker_type stays provider-neutral for
        # external_cli; Codex retains legacy worker_type=codex.
        held_leases: list[tuple[str, int]] = []
        needs_lease = bool(getattr(worker, "requires_execution_lease", False)) or getattr(
            worker, "worker_type", ""
        ) in {"codex", "external_cli"}
        if needs_lease:
            db_path = getattr(worker, "canonical_db_path", None) or context.get(
                "CANONICAL_DB_PATH"
            )
            if db_path:
                assert_canonical_db_outside_worktree(db_path, worktree)
                context["CANONICAL_DB_PATH"] = str(db_path)
            now = _utcnow()
            resources = [
                worktree_resource_key(worktree),
                run_node_resource_key(run_id, attempt.node),
            ]
            try:
                with self.runtime.store.transaction() as conn:
                    for resource in resources:
                        token = self.runtime.store.acquire_execution_lease(
                            resource_key=resource,
                            attempt_id=attempt.attempt_id,
                            run_id=run_id,
                            node=attempt.node,
                            now=now,
                            expires_at=_iso_plus_seconds(now, lease_ttl_sec),
                            lease_id=_new_id("lease"),
                            conn=conn,
                        )
                        held_leases.append((resource, int(token)))
                    # Primary fencing token is the worktree lease generation.
                    attempt.fencing_token = held_leases[0][1]
                    self.runtime.store.update_attempt(attempt, conn=conn)
            except (
                LeaseBusyError,
                PreviousWorkerStillAliveError,
                PreviousWorkerUnverifiableError,
            ) as exc:
                blocker = getattr(exc, "blocker", None) or (
                    "previous_worker_still_alive"
                    if isinstance(exc, PreviousWorkerStillAliveError)
                    else "previous_worker_unverifiable"
                    if isinstance(exc, PreviousWorkerUnverifiableError)
                    else "lease_busy"
                )
                attempt.status = "rejected"
                attempt.ended_at = _utcnow()
                with self.runtime.store.transaction() as conn:
                    self.runtime.store.update_attempt(attempt, conn=conn)
                return IngestResult(
                    apply=DurableApplyResult(
                        accepted=False,
                        duplicate=False,
                        run=self.runtime.get_run(run_id),
                        reason=str(exc),
                        blocker=blocker,
                    ),
                    attempt=attempt,
                )

        try:
            if write_context and run.worktree:
                write_worker_context(
                    run.worktree,
                    run=run,
                    attempt=attempt,
                    goal_objective=goal.objective if goal else None,
                )
                if isinstance(worker, FakeWorkerAdapter):
                    result = worker.execute(run=run, attempt=attempt, context=context)
                    # Controller-fixed path only.
                    write_worker_result(safe_result_path(run.worktree), result)
                else:
                    result = worker.execute(run=run, attempt=attempt, context=context)
            else:
                result = worker.execute(run=run, attempt=attempt, context=context)

            launch = getattr(worker, "last_launch", None)
            if launch is not None and getattr(launch, "pid", None):
                from .process_identity import read_process_identity

                attempt.worker_pid = int(launch.pid)
                identity = read_process_identity(int(launch.pid))
                with self.runtime.store.transaction() as conn:
                    self.runtime.store.update_attempt(attempt, conn=conn)
                    if identity is not None and held_leases:
                        for resource, token in held_leases:
                            self.runtime.store.bind_execution_identity(
                                resource_key=resource,
                                attempt_id=attempt.attempt_id,
                                fencing_token=int(token),
                                identity=identity,
                                conn=conn,
                            )

            mark = None
            if (
                result.proposed_outcome
                and result.proposed_outcome.outcome_type == "BUILD_COMPLETED"
            ):
                mark = result.proposed_outcome.head_sha
            out = self.ingest_worker_result(
                run_id=run_id,
                attempt_id=attempt.attempt_id,
                result=result,
                mark_tested_sha=mark,
            )
            return out
        finally:
            if held_leases:
                now = _utcnow()
                with self.runtime.store.transaction() as conn:
                    for resource, token in held_leases:
                        self.runtime.store.release_execution_lease(
                            resource_key=resource,
                            attempt_id=attempt.attempt_id,
                            fencing_token=int(token),
                            now=now,
                            conn=conn,
                        )

    def observe_worktree_lease(self, run_id: str) -> dict[str, Any]:
        """Observe worktree lease liveness for a Run (no mutation)."""
        from .canonical_paths import worktree_resource_key
        from .process_identity import ProcessIdentity, classify_owner_liveness

        run = self.runtime.get_run(run_id)
        worktree = run.worktree or ""
        if not worktree:
            return {
                "run_id": run_id,
                "resource_key": None,
                "lease": None,
                "liveness": "no_worktree",
                "recovery": "bind_worktree",
            }
        resource = worktree_resource_key(worktree)
        lease = self.runtime.store.get_active_lease(resource)
        if lease is None:
            return {
                "run_id": run_id,
                "resource_key": resource,
                "lease": None,
                "liveness": "none",
                "recovery": "step_ok",
            }
        identity_status = lease.get("identity_status") or "pending"
        stored = ProcessIdentity.from_mapping(
            self.runtime.store._lease_row_identity(lease)  # noqa: SLF001 — shared store helper
        )
        liveness = (
            classify_owner_liveness(stored) if identity_status == "bound" else "unverifiable"
        )
        if liveness == "alive":
            recovery = "wait"
        elif liveness == "dead":
            recovery = "reclaim_and_step"
        else:
            recovery = "reconcile_required"
        return {
            "run_id": run_id,
            "resource_key": resource,
            "lease": {
                "lease_id": lease.get("lease_id"),
                "owner": lease.get("owner"),
                "fencing_token": lease.get("fencing_token"),
                "expires_at": lease.get("expires_at"),
                "identity_status": identity_status,
                "worker_pid": lease.get("worker_pid"),
            },
            "liveness": liveness,
            "recovery": recovery,
            "founder_required": False,
        }

    def recover_and_step(
        self,
        run_id: str,
        *,
        worker: Optional[WorkerAdapter] = None,
        model_profile: Optional[str] = None,
        lease_ttl_sec: float = DEFAULT_LEASE_TTL_SEC,
        extra_context: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """If prior worker is dead, reclaim via step; if alive, wait (no Founder).

        Reuses existing lease CAS / fencing — does not invent a second orchestrator.
        """
        observation = self.observe_worktree_lease(run_id)
        if observation.get("recovery") == "wait":
            return {
                "accepted": False,
                "action": "wait_prior_worker_alive",
                "founder_required": False,
                "observation": observation,
                "step": None,
            }
        if observation.get("recovery") == "reconcile_required":
            return {
                "accepted": False,
                "action": "reconcile_required",
                "founder_required": False,
                "observation": observation,
                "step": None,
            }
        stepped = self.step(
            run_id,
            worker=worker,
            model_profile=model_profile,
            lease_ttl_sec=lease_ttl_sec,
            extra_context=extra_context,
        )
        return {
            "accepted": bool(stepped.apply.accepted or stepped.duplicate_ingest),
            "action": "reclaim_and_step" if observation.get("liveness") == "dead" else "step",
            "founder_required": False,
            "observation": observation,
            "step": stepped.to_dict(),
        }
