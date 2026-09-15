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
from .sqlite_store import SqliteControlPlaneStore, StaleStateError


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
            # Apply creation event inside same transaction (trusted bootstrap).
            result = self._apply_in_tx(
                conn,
                run_id=run_id,
                canonical=create_event,
                ingest_key=None,
                expected_state_version=0,
            )
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

    def reconstruct_projection(self, run_id: str) -> dict[str, Any]:
        """Rebuild graph-relevant Run fields from append-only events only."""
        run = self.get_run(run_id)
        state = self.task_state(run_id)
        projected = self._project(
            Run(
                run_id=run.run_id,
                goal_id=run.goal_id,
                project=run.project,
                graph_version=run.graph_version,
                risk_tier=run.risk_tier,
                status=run.status,
                current_node=run.current_node,
                worktree=run.worktree,
                branch=run.branch,
                base_sha=run.base_sha,
                head_sha=run.head_sha,
                tested_sha=run.tested_sha,
                created_at=run.created_at,
                updated_at=run.updated_at,
                blocker=run.blocker,
                closed=run.closed,
                stopped=run.stopped,
                human_approved=run.human_approved,
                graph_snapshot=dict(run.graph_snapshot),
                state_version=run.state_version,
            ),
            state,
            updated_at=run.updated_at,
        )
        return {
            "current_node": projected.current_node,
            "status": projected.status,
            "base_sha": projected.base_sha,
            "head_sha": projected.head_sha,
            "blocker": projected.blocker,
            "closed": projected.closed,
            "stopped": projected.stopped,
            "human_approved": projected.human_approved,
            "graph_snapshot": projected.graph_snapshot,
        }

    def verify_projection_matches_events(self, run_id: str) -> dict[str, Any]:
        """Compare persisted Run projection vs event-replay reconstruction."""
        run = self.get_run(run_id)
        reconstructed = self.reconstruct_projection(run_id)
        persisted = {
            "current_node": run.current_node,
            "status": run.status,
            "base_sha": run.base_sha,
            "head_sha": run.head_sha,
            "blocker": run.blocker,
            "closed": run.closed,
            "stopped": run.stopped,
            "human_approved": run.human_approved,
            "graph_snapshot": run.graph_snapshot,
        }
        return {
            "equal": persisted == reconstructed,
            "persisted": persisted,
            "reconstructed": reconstructed,
        }

    def bind_worktree(
        self,
        run_id: str,
        *,
        worktree: str,
        branch: str,
        base_sha: Optional[str] = None,
    ) -> Run:
        with self.store.transaction() as conn:
            run = self.store.get_run(run_id, conn=conn)
            if run is None:
                raise KeyError(f"unknown run_id: {run_id}")
            expected = run.state_version
            now = _utcnow()
            run.worktree = worktree
            run.branch = branch
            if base_sha:
                run.base_sha = base_sha
                if not run.head_sha:
                    run.head_sha = base_sha
            run.updated_at = now
            self.store.update_run_projection(run, expected_version=expected, conn=conn)
            return run

    def start_attempt(
        self,
        run_id: str,
        *,
        worker_type: str,
        model_profile: Optional[str] = None,
        worker_pid: Optional[int] = None,
        attempt_id: Optional[str] = None,
    ) -> Attempt:
        with self.store.transaction() as conn:
            run = self.store.get_run(run_id, conn=conn)
            if run is None:
                raise KeyError(f"unknown run_id: {run_id}")
            if run.closed or run.stopped:
                raise RuntimeError(f"run {run_id} is terminal (status={run.status})")
            if not run.current_node or run.current_node in ("close", "approved_for_effect"):
                raise RuntimeError(
                    f"no runnable node for run {run_id} (current_node={run.current_node})"
                )
            if run.current_node == "human_gate" or run.status == "waiting_for_approval":
                raise RuntimeError(
                    f"run {run_id} is waiting_for_approval; use graph approve (not worker step)"
                )
            # Bind the graph snapshot version the worker is authorized to advance.
            expected_state_version = int(run.state_version)
            now = _utcnow()
            attempt = Attempt(
                attempt_id=attempt_id or _new_id("att"),
                run_id=run_id,
                node=run.current_node,
                worker_type=worker_type,
                model_profile=model_profile,
                worker_pid=worker_pid,
                expected_state_version=expected_state_version,
                started_at=now,
                status="started",
            )
            self.store.insert_attempt(attempt, conn=conn)
            # Ephemeral waiting status must not consume state_version.
            self.store.update_run_ephemeral_status(
                run_id, status="waiting_worker", updated_at=now, conn=conn
            )
            return attempt

    def apply_graph_event(
        self,
        *,
        run_id: str,
        event: Event,
        expected_state_version: int,
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
            return self._apply_in_tx(
                conn,
                run_id=run_id,
                canonical=canonical,
                ingest_key=ingest_key,
                expected_state_version=expected_state_version,
            )

    def _apply_in_tx(
        self,
        conn,
        *,
        run_id: str,
        canonical: CanonicalEvent,
        ingest_key: Optional[str],
        expected_state_version: int,
    ) -> DurableApplyResult:
        # All reads below occur inside the caller's BEGIN IMMEDIATE transaction.
        run = self.store.get_run(run_id, conn=conn)
        if run is None:
            raise KeyError(f"unknown run_id: {run_id}")

        if run.state_version != expected_state_version:
            return DurableApplyResult(
                accepted=False,
                duplicate=False,
                run=run,
                event=canonical,
                reason=(
                    f"stale state_version: expected {expected_state_version} "
                    f"got {run.state_version}"
                ),
                blocker="stale_state_version",
            )

        existing = self.store.get_event(canonical.event_id)
        if existing is not None:
            if not _same_logical_event(existing, canonical):
                return DurableApplyResult(
                    accepted=False,
                    duplicate=True,
                    run=run,
                    event=existing,
                    reason="duplicate event_id with differing payload",
                )
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
        expected_version = run.state_version

        if not check.accepted:
            if check.blocker and _is_persisted_stop_blocker(check.blocker):
                stop = self._build_stop_event(graph_event, state, check)
                stop_canonical = self._graph_event_to_canonical(
                    stop, attempt_id=canonical.attempt_id, evidence_refs=canonical.evidence_refs
                )
                stored_stop = self.store.append_event(stop_canonical, ingest_key=None, conn=conn)
                new_state = reduce(prior + [stop])
                run = self._project(run, new_state, updated_at=canonical.created_at)
                try:
                    self.store.update_run_projection(
                        run, expected_version=expected_version, conn=conn
                    )
                except StaleStateError as exc:
                    return DurableApplyResult(
                        accepted=False,
                        duplicate=False,
                        run=self.store.get_run(run_id, conn=conn) or run,
                        event=canonical,
                        reason=str(exc),
                        blocker="stale_state_version",
                    )
                return DurableApplyResult(
                    accepted=False,
                    duplicate=False,
                    run=run,
                    event=stored_stop,
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

        stored = self.store.append_event(canonical, ingest_key=ingest_key, conn=conn)
        new_state = reduce(prior + [graph_event])
        if new_state.task_status == "closed_success" and not can_close_successfully(new_state):
            raise RuntimeError("invariant violated: closed_success without valid human approval")
        run = self._project(run, new_state, updated_at=canonical.created_at)
        try:
            self.store.update_run_projection(run, expected_version=expected_version, conn=conn)
        except StaleStateError as exc:
            return DurableApplyResult(
                accepted=False,
                duplicate=False,
                run=self.store.get_run(run_id, conn=conn) or run,
                event=canonical,
                reason=str(exc),
                blocker="stale_state_version",
            )
        return DurableApplyResult(
            accepted=True,
            duplicate=False,
            run=run,
            event=stored,
            reason=None,
            blocker=new_state.blocker,
        )

    def _project(self, run: Run, state: TaskState, *, updated_at: str) -> Run:
        status = state.task_status
        if status == "pending":
            status = "pending"
        elif status in ("investigating", "building", "reviewing"):
            status = "running"
        elif status in ("waiting_for_approval", "human_approval_required"):
            status = "waiting_for_approval"
        elif status == "approved_for_effect":
            status = "approved_for_effect"
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

    def ingest_observation(
        self,
        *,
        run_id: str,
        fact: "ObservableFact",
        repository: Optional[str] = None,
    ) -> DurableApplyResult:
        """Observation → verifier → Event → reducer (idempotent)."""
        from .observation import FACT_TYPES, fact_event_id, serialize_fact_evidence

        if fact.fact_type not in FACT_TYPES:
            return DurableApplyResult(
                accepted=False,
                duplicate=False,
                run=self.get_run(run_id),
                reason=f"unknown fact_type: {fact.fact_type}",
                blocker="invalid_observation",
            )
        if not fact.observed_head_sha:
            return DurableApplyResult(
                accepted=False,
                duplicate=False,
                run=self.get_run(run_id),
                reason="observation requires observed_head_sha",
                blocker="invalid_observation",
            )
        run = self.get_run(run_id)
        if run.closed:
            return DurableApplyResult(
                accepted=False,
                duplicate=False,
                run=run,
                reason="run already closed",
            )
        if not run.current_node:
            return DurableApplyResult(
                accepted=False,
                duplicate=False,
                run=run,
                reason="run has no current_node",
            )
        event = Event(
            event_id=fact_event_id(run_id, fact),
            task_id=run_id,
            timestamp=fact.observed_at or _utcnow(),
            event_type="EXTERNAL_OBSERVATION",
            node=run.current_node,
            actor_id="observer",
            actor_role="system",
            repository=repository
            or (run.graph_snapshot or {}).get("repository")
            or f"jerry200176-png/{run.project}",
            base_sha=run.base_sha,
            head_sha=fact.observed_head_sha,
            conclusion=fact.fact_type,
            evidence=serialize_fact_evidence(fact),
        )
        return self.apply_graph_event(
            run_id=run_id, event=event, expected_state_version=run.state_version
        )

    def grant_founder_approval(
        self,
        *,
        run_id: str,
        action: str,
        head_sha: str,
        actor: str = "founder",
        scope: Optional[str] = None,
        external_ref: Optional[str] = None,
        expires_at: Optional[str] = None,
        approval_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """Trusted control-plane path: durable Approval + HUMAN_APPROVED.

        Workers cannot call this. Head SHA must match current Run head.
        """
        from .durable_models import Approval
        from .reducer import approval_still_valid

        run = self.get_run(run_id)
        if run.current_node != "human_gate":
            return {
                "accepted": False,
                "reason": f"approval requires current_node=human_gate, got {run.current_node}",
                "run": run.to_dict(),
            }
        if not head_sha or head_sha != run.head_sha:
            return {
                "accepted": False,
                "reason": (
                    f"approval head_sha {head_sha!r} does not match run head_sha {run.head_sha!r}"
                ),
                "blocker": "approval_head_mismatch",
                "run": run.to_dict(),
            }
        now = _utcnow()
        scope = scope or f"{action}@{head_sha}"
        approval = Approval(
            approval_id=approval_id or _new_id("appr"),
            run_id=run_id,
            action=action,
            scope=scope,
            created_at=now,
            status="granted",
            actor=actor,
            bound_head_sha=head_sha,
            expires_at=expires_at,
            decided_at=now,
            external_ref=external_ref,
        )
        event = Event(
            event_id=f"{run_id}:HUMAN_APPROVED:{approval.approval_id}",
            task_id=run_id,
            timestamp=now,
            event_type="HUMAN_APPROVED",
            node="human_gate",
            actor_id=actor,
            actor_role="human",
            repository=(run.graph_snapshot or {}).get("repository")
            or f"jerry200176-png/{run.project}",
            base_sha=run.base_sha,
            head_sha=head_sha,
            conclusion=action,
            evidence={
                "approval_id": approval.approval_id,
                "action": action,
                "scope": scope,
                "bound_head_sha": head_sha,
                "external_ref": external_ref,
                "source": "control_plane_cli",
            },
        )
        with self.store.transaction() as conn:
            self.store.insert_approval(approval, conn=conn)
            # Apply inside same process; apply_event opens its own tx — so apply after commit.
        apply = self.apply_graph_event(
            run_id=run_id, event=event, expected_state_version=run.state_version
        )
        if not apply.accepted and not apply.duplicate:
            # Mark approval superseded if graph rejected.
            approval_bad = Approval(
                approval_id=approval.approval_id,
                run_id=approval.run_id,
                action=approval.action,
                scope=approval.scope,
                created_at=approval.created_at,
                status="superseded",
                actor=approval.actor,
                bound_head_sha=approval.bound_head_sha,
                expires_at=approval.expires_at,
                decided_at=now,
                external_ref=approval.external_ref,
            )
            self.store.update_approval(approval_bad)
        run2 = self.get_run(run_id)
        return {
            "accepted": apply.accepted or apply.duplicate,
            "duplicate": apply.duplicate,
            "reason": apply.reason,
            "blocker": apply.blocker,
            "approval": approval.to_dict(),
            "approval_valid": approval_still_valid(
                TaskState(
                    human_approved=run2.human_approved,
                    approved_head_sha=(run2.graph_snapshot or {}).get("approved_head_sha"),
                    head_sha=run2.head_sha,
                )
            )
            if apply.accepted or apply.duplicate
            else False,
            "run": run2.to_dict(),
            "apply": apply.to_dict(),
        }


    def execute_approved_effect(
        self,
        *,
        run_id: str,
        action: str,
        repo: str,
        target: str,
        mutator: Any,
        params: Optional[dict[str, Any]] = None,
        require_ci: bool = False,
        observed_head_sha: Optional[str] = None,
    ) -> dict[str, Any]:
        """Execute allowlisted effect after approval, with TOCTOU re-check.

        Production deploy actions are rejected by allowlist before mutation.
        """
        from .effect_journal import DurableEffectJournal, effect_identity
        from .observation import ci_authorizes_head
        from .reducer import approval_still_valid, reduce

        params = params or {}
        run = self.get_run(run_id)
        if run.current_node != "approved_for_effect":
            return {
                "accepted": False,
                "reason": f"effects require node=approved_for_effect, got {run.current_node}",
                "run": run.to_dict(),
            }
        eid = effect_identity(
            run_id=run_id,
            action=action,
            repo=repo,
            target=target,
            head_sha=run.head_sha or "",
        )
        existing = self.store.get_effect(eid)
        if existing is not None and existing.status == "succeeded":
            return {
                "accepted": True,
                "duplicate": True,
                "effect": existing.to_dict(),
                "run": run.to_dict(),
            }
        events = [self._canonical_to_graph(e) for e in self.list_events(run_id)]
        state = reduce(events)
        if not approval_still_valid(state):
            return {
                "accepted": False,
                "reason": "approval invalid or head_sha drifted",
                "blocker": "stale_approval",
                "run": run.to_dict(),
            }
        if observed_head_sha and observed_head_sha != run.head_sha:
            return {
                "accepted": False,
                "reason": "TOCTOU: observed_head_sha != run.head_sha",
                "blocker": "toctou_head_mismatch",
                "run": run.to_dict(),
            }
        if require_ci:
            obs = (run.graph_snapshot or {}).get("observations") or {}
            if not ci_authorizes_head(obs, run.head_sha or ""):
                return {
                    "accepted": False,
                    "reason": "CI not green for current head_sha",
                    "blocker": "ci_not_green",
                    "run": run.to_dict(),
                }
        approvals = [a for a in self.store.list_approvals(run_id) if a.status == "granted"]
        if not approvals:
            return {
                "accepted": False,
                "reason": "no granted approval to consume",
                "blocker": "approval_missing",
                "run": run.to_dict(),
            }
        approval = approvals[-1]
        if approval.bound_head_sha and approval.bound_head_sha != run.head_sha:
            return {
                "accepted": False,
                "reason": "approval bound_head_sha mismatch",
                "blocker": "stale_approval",
                "run": run.to_dict(),
            }
        journal = DurableEffectJournal(self.store, mutator)
        effect = journal.declare(
            run_id=run_id,
            action=action,
            repo=repo,
            target=target,
            head_sha=run.head_sha or "",
            approval_id=approval.approval_id,
        )
        if effect.status == "succeeded":
            return {
                "accepted": True,
                "duplicate": True,
                "effect": effect.to_dict(),
                "run": run.to_dict(),
            }
        journal.prepare(
            effect.effect_id,
            precheck={
                "run_head_sha": run.head_sha,
                "observed_head_sha": observed_head_sha,
                "approval_id": approval.approval_id,
                "require_ci": require_ci,
            },
        )
        try:
            effect = journal.execute(effect.effect_id, params=params)
        except Exception as exc:  # noqa: BLE001
            effect = self.store.get_effect(effect.effect_id)
            return {
                "accepted": False,
                "reason": str(exc),
                "blocker": getattr(effect, "status", None) if effect else "effect_failed",
                "effect": effect.to_dict() if effect else None,
                "run": self.get_run(run_id).to_dict(),
            }
        consumed = self.store.consume_approval(
            approval.approval_id, effect_id=effect.effect_id, now=_utcnow()
        )
        return {
            "accepted": True,
            "duplicate": False,
            "approval_consumed": consumed,
            "effect": effect.to_dict(),
            "run": self.get_run(run_id).to_dict(),
        }


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
            run_event_seq=0,  # allocated on append
            attempt_id=attempt_id,
            type=event.event_type,
            payload=payload,
            evidence_refs=evidence_refs,
            created_at=event.timestamp,
        )

    @staticmethod
    def _canonical_to_graph(event: CanonicalEvent) -> Event:
        payload = dict(event.payload)
        # Envelope fields are authoritative for replay (payload is supporting detail).
        payload["event_id"] = event.event_id
        payload["task_id"] = event.run_id
        payload["event_type"] = event.type
        payload["timestamp"] = event.created_at
        return Event.from_dict(payload)


def _same_logical_event(left: CanonicalEvent, right: CanonicalEvent) -> bool:
    """Compare event identity/payload; sequence numbers are allocation metadata."""
    return (
        left.event_id == right.event_id
        and left.run_id == right.run_id
        and left.type == right.type
        and left.payload == right.payload
        and left.attempt_id == right.attempt_id
        and list(left.evidence_refs) == list(right.evidence_refs)
    )
