"""Durable graph runtime: SQLite event log + v0 router/reducer.

Workers never UPDATE runs. Transitions commit only through this runtime.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional

from .durable_models import GRAPH_VERSION, Attempt, CanonicalEvent, Goal, Run
from .models import Event, TaskState
from .reducer import can_close_successfully, reduce
from .router import TransitionResult, validate_transition
from .runtime import _is_persisted_stop_blocker
from .sqlite_store import SqliteControlPlaneStore


def _utcnow() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex}"


@dataclass
class DurableApplyResult:
    accepted: bool
    duplicate: bool
    run: Run
    event: Optional[CanonicalEvent] = None
    reason: Optional[str] = None
    blocker: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "accepted": self.accepted,
            "duplicate": self.duplicate,
            "reason": self.reason,
            "blocker": self.blocker,
            "event_id": self.event.event_id if self.event else None,
            "run": self.run.to_dict(),
        }


class DurableGraphRuntime:
    """Process-independent runtime over a control-plane SQLite database."""

    def __init__(self, store: SqliteControlPlaneStore) -> None:
        self.store = store

    def close(self) -> None:
        self.store.close()

    def create_run(
        self,
        *,
        objective: str,
        project: str,
        risk_tier: str = "low",
        success_condition: Optional[str] = None,
        repository: str = "jerry200176-png/portfolio-ops",
        base_sha: Optional[str] = None,
        worktree: Optional[str] = None,
        branch: Optional[str] = None,
        goal_id: Optional[str] = None,
        run_id: Optional[str] = None,
    ) -> Run:
        now = _utcnow()
        goal_id = goal_id or _new_id("goal")
        run_id = run_id or _new_id("run")
        goal = Goal(
            goal_id=goal_id,
            objective=objective,
            project=project,
            risk_tier=risk_tier,
            success_condition=success_condition,
            created_at=now,
        )
        run = Run(
            run_id=run_id,
            goal_id=goal_id,
            project=project,
            graph_version=GRAPH_VERSION,
            risk_tier=risk_tier,
            status="pending",
            current_node="intake",
            worktree=worktree,
            branch=branch,
            base_sha=base_sha,
            head_sha=base_sha,
            created_at=now,
            updated_at=now,
        )
        create_event = self._graph_event_to_canonical(
            Event(
                event_id=f"{run_id}:TASK_CREATED",
                task_id=run_id,
                timestamp=now,
                event_type="TASK_CREATED",
                node="intake",
                actor_id="system",
                actor_role="system",
                repository=repository,
                base_sha=base_sha,
                head_sha=base_sha,
                conclusion="created",
                evidence={"objective": objective},
            ),
            attempt_id=None,
            evidence_refs=(),
        )

        with self.store.transaction() as conn:
            self.store.insert_goal(goal, conn=conn)
            self.store.insert_run(run, conn=conn)
            # Apply creation event inside same transaction
            result = self._apply_in_tx(conn, run_id=run_id, canonical=create_event, ingest_key=None)
            if not result.accepted:
                raise RuntimeError(f"failed to create run: {result.reason}")
            return result.run

    def get_run(self, run_id: str) -> Run:
        run = self.store.get_run(run_id)
        if run is None:
            raise KeyError(f"unknown run_id: {run_id}")
        return run

    def list_events(self, run_id: str) -> list[CanonicalEvent]:
        return self.store.list_events(run_id)

    def task_state(self, run_id: str) -> TaskState:
        return reduce([self._canonical_to_graph(e) for e in self.store.list_events(run_id)])

    def bind_worktree(
        self,
        run_id: str,
        *,
        worktree: str,
        branch: str,
        base_sha: Optional[str] = None,
    ) -> Run:
        run = self.get_run(run_id)
        now = _utcnow()
        run.worktree = worktree
        run.branch = branch
        if base_sha:
            run.base_sha = base_sha
            if not run.head_sha:
                run.head_sha = base_sha
        run.updated_at = now
        with self.store.transaction() as conn:
            self.store.update_run_projection(run, conn=conn)
        return self.get_run(run_id)

    def start_attempt(
        self,
        run_id: str,
        *,
        worker_type: str,
        model_profile: Optional[str] = None,
        worker_pid: Optional[int] = None,
        attempt_id: Optional[str] = None,
    ) -> Attempt:
        run = self.get_run(run_id)
        if run.closed or run.stopped:
            raise RuntimeError(f"run {run_id} is terminal (status={run.status})")
        if not run.current_node or run.current_node in ("close",):
            raise RuntimeError(f"no runnable node for run {run_id} (current_node={run.current_node})")
        now = _utcnow()
        attempt = Attempt(
            attempt_id=attempt_id or _new_id("att"),
            run_id=run_id,
            node=run.current_node,
            worker_type=worker_type,
            model_profile=model_profile,
            worker_pid=worker_pid,
            started_at=now,
            status="started",
        )
        run.status = "waiting_worker"
        run.updated_at = now
        with self.store.transaction() as conn:
            self.store.insert_attempt(attempt, conn=conn)
            self.store.update_run_projection(run, conn=conn)
        return attempt

    def apply_graph_event(
        self,
        *,
        run_id: str,
        event: Event,
        attempt_id: Optional[str] = None,
        evidence_refs: tuple[str, ...] = (),
        ingest_key: Optional[str] = None,
    ) -> DurableApplyResult:
        if event.task_id != run_id:
            raise ValueError("event.task_id must equal run_id")
        canonical = self._graph_event_to_canonical(
            event, attempt_id=attempt_id, evidence_refs=evidence_refs
        )
        with self.store.transaction() as conn:
            return self._apply_in_tx(conn, run_id=run_id, canonical=canonical, ingest_key=ingest_key)

    def _apply_in_tx(
        self,
        conn,
        *,
        run_id: str,
        canonical: CanonicalEvent,
        ingest_key: Optional[str],
    ) -> DurableApplyResult:
        existing = self.store.get_event(canonical.event_id)
        if existing is not None:
            if existing.to_dict() != canonical.to_dict():
                run = self.store.get_run(run_id)
                assert run is not None
                return DurableApplyResult(
                    accepted=False,
                    duplicate=True,
                    run=run,
                    event=existing,
                    reason="duplicate event_id with differing payload",
                )
            run = self.store.get_run(run_id)
            assert run is not None
            return DurableApplyResult(
                accepted=True,
                duplicate=True,
                run=run,
                event=existing,
                reason="duplicate event_id (idempotent)",
            )

        if ingest_key:
            by_key = self.store.get_event_by_ingest_key(ingest_key)
            if by_key is not None:
                run = self.store.get_run(run_id)
                assert run is not None
                if by_key.event_id == canonical.event_id:
                    return DurableApplyResult(
                        accepted=True,
                        duplicate=True,
                        run=run,
                        event=by_key,
                        reason="duplicate ingest_key (idempotent)",
                    )
                return DurableApplyResult(
                    accepted=False,
                    duplicate=True,
                    run=run,
                    event=by_key,
                    reason="ingest_key already used by a different event",
                )

        # Rebuild state from durable events (source of truth), not from process memory.
        prior = [self._canonical_to_graph(e) for e in self.store.list_events(run_id)]
        state = reduce(prior)
        graph_event = self._canonical_to_graph(canonical)
        check: TransitionResult = validate_transition(state, graph_event)
        run = self.store.get_run(run_id)
        assert run is not None

        if not check.accepted:
            if check.blocker and _is_persisted_stop_blocker(check.blocker):
                stop = self._build_stop_event(graph_event, state, check)
                stop_canonical = self._graph_event_to_canonical(
                    stop, attempt_id=canonical.attempt_id, evidence_refs=canonical.evidence_refs
                )
                self.store.append_event(stop_canonical, ingest_key=None, conn=conn)
                new_state = reduce(prior + [stop])
                run = self._project(run, new_state, updated_at=canonical.created_at)
                self.store.update_run_projection(run, conn=conn)
                return DurableApplyResult(
                    accepted=False,
                    duplicate=False,
                    run=run,
                    event=stop_canonical,
                    reason=check.reason,
                    blocker=check.blocker,
                )
            return DurableApplyResult(
                accepted=False,
                duplicate=False,
                run=run,
                event=canonical,
                reason=check.reason,
                blocker=check.blocker,
            )

        self.store.append_event(canonical, ingest_key=ingest_key, conn=conn)
        new_state = reduce(prior + [graph_event])
        if new_state.task_status == "closed_success" and not can_close_successfully(new_state):
            raise RuntimeError("invariant violated: closed_success without valid human approval")
        run = self._project(run, new_state, updated_at=canonical.created_at)
        self.store.update_run_projection(run, conn=conn)
        return DurableApplyResult(
            accepted=True,
            duplicate=False,
            run=run,
            event=canonical,
            reason=None,
            blocker=new_state.blocker,
        )

    def _project(self, run: Run, state: TaskState, *, updated_at: str) -> Run:
        status = state.task_status
        if status == "pending":
            status = "pending"
        elif status in ("investigating", "building", "reviewing"):
            status = "running"
        elif status == "human_approval_required":
            status = "human_approval_required"
        elif status == "closed_success":
            status = "closed_success"
        elif status == "closed_blocked":
            status = "closed_blocked"
        elif status == "blocked":
            status = "blocked"

        run.status = status
        run.current_node = state.current_node
        run.base_sha = state.base_sha or run.base_sha
        run.head_sha = state.head_sha or run.head_sha
        run.blocker = state.blocker
        run.closed = state.closed
        run.stopped = state.stopped
        run.human_approved = state.human_approved
        run.graph_snapshot = state.snapshot()
        run.updated_at = updated_at
        return run

    def _build_stop_event(self, triggering_event: Event, state: TaskState, check: TransitionResult) -> Event:
        retry_count = state.retry_count.get(triggering_event.node, 0)
        failure_signature = None
        if triggering_event.evidence:
            failure_signature = triggering_event.evidence.get("failure_signature")
        return Event(
            event_id=f"{triggering_event.event_id}:graph-stopped",
            task_id=triggering_event.task_id,
            timestamp=triggering_event.timestamp,
            event_type="GRAPH_STOPPED",
            node=triggering_event.node,
            actor_id="system",
            actor_role="system",
            repository=triggering_event.repository,
            base_sha=state.base_sha or triggering_event.base_sha,
            head_sha=state.head_sha or triggering_event.head_sha,
            conclusion="stopped",
            evidence={
                "reason": check.reason,
                "blocker": check.blocker,
                "failure_signature": failure_signature,
                "retry_count": retry_count,
                "agent_run_count": state.agent_run_count,
                "trigger_event_id": triggering_event.event_id,
                "trigger_event_type": triggering_event.event_type,
            },
        )

    @staticmethod
    def _graph_event_to_canonical(
        event: Event,
        *,
        attempt_id: Optional[str],
        evidence_refs: tuple[str, ...],
    ) -> CanonicalEvent:
        payload = event.to_dict()
        return CanonicalEvent(
            event_id=event.event_id,
            run_id=event.task_id,
            attempt_id=attempt_id,
            type=event.event_type,
            payload=payload,
            evidence_refs=evidence_refs,
            created_at=event.timestamp,
        )

    @staticmethod
    def _canonical_to_graph(event: CanonicalEvent) -> Event:
        payload = dict(event.payload)
        # Prefer payload fields; fall back to envelope.
        payload.setdefault("event_id", event.event_id)
        payload.setdefault("task_id", event.run_id)
        payload.setdefault("event_type", event.type)
        payload.setdefault("timestamp", event.created_at)
        return Event.from_dict(payload)
