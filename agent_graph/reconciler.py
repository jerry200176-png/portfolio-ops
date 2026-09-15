"""Bounded reconciler: desired graph state vs observed external facts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from .durable_runtime import DurableGraphRuntime
from .github_observe import GitHubReader, observe_pull_request
from .models import Event
from .observation import ci_authorizes_head
from .reducer import approval_still_valid, reduce


@dataclass
class ReconcileResult:
    run_id: str
    actions: list[str]
    run: dict[str, Any]
    closed: bool = False
    reason: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "actions": self.actions,
            "closed": self.closed,
            "reason": self.reason,
            "run": self.run,
        }


class GraphReconciler:
    def __init__(self, runtime: DurableGraphRuntime, reader: GitHubReader) -> None:
        self.runtime = runtime
        self.reader = reader

    def reconcile_run(
        self,
        run_id: str,
        *,
        pr_number: Optional[int] = None,
        repo: Optional[str] = None,
    ) -> ReconcileResult:
        run = self.runtime.get_run(run_id)
        actions: list[str] = []
        repo = repo or f"jerry200176-png/{run.project}"
        if pr_number is not None:
            facts = observe_pull_request(repo=repo, pr_number=pr_number, reader=self.reader)
            for fact in facts:
                out = self.runtime.ingest_observation(run_id=run_id, fact=fact, repository=repo)
                if out.accepted and not out.duplicate:
                    actions.append(f"observed:{fact.fact_type}")
                elif out.duplicate:
                    actions.append(f"dup:{fact.fact_type}")

        run = self.runtime.get_run(run_id)
        obs = (run.graph_snapshot or {}).get("observations") or {}
        latest = obs.get("latest_by_type") or {}

        # Ambiguous effects: if PR merged externally, mark effect succeeded.
        for eff in self.runtime.store.list_effects(run_id):
            if eff.status in ("executing", "ambiguous") and eff.action == "github_pr_merge":
                if "PR_MERGED_EXTERNALLY" in latest:
                    self.runtime.store.get_effect  # noqa: keep store hot
                    from .effect_journal import DurableEffectJournal
                    from .github_mutate import FakeGitHubMutator

                    # Reconcile without re-mutating.
                    journal = DurableEffectJournal(self.runtime.store, FakeGitHubMutator())
                    journal.mark_reconciled_success(
                        eff.effect_id,
                        evidence={"via": "PR_MERGED_EXTERNALLY", "latest": latest},
                    )
                    actions.append(f"effect_reconciled:{eff.effect_id}")

        run = self.runtime.get_run(run_id)
        # Close when approved_for_effect and merge observed at matching head.
        if run.current_node == "approved_for_effect" and "PR_MERGED_EXTERNALLY" in latest:
            merged_sha = (latest.get("PR_MERGED_EXTERNALLY") or {}).get("observed_head_sha")
            if merged_sha and run.head_sha and merged_sha != run.head_sha:
                return ReconcileResult(
                    run_id=run_id,
                    actions=actions,
                    run=run.to_dict(),
                    reason="merged head does not match run head_sha; fail closed",
                )
            event = Event(
                event_id=f"{run_id}:EFFECT_RECONCILED:merge",
                task_id=run_id,
                timestamp=run.updated_at,
                event_type="EFFECT_RECONCILED",
                node="approved_for_effect",
                actor_id="reconciler",
                actor_role="system",
                repository=repo,
                base_sha=run.base_sha,
                head_sha=run.head_sha,
                conclusion="merged_externally",
                evidence={"source": "reconciler", "observations": latest},
            )
            apply = self.runtime.apply_graph_event(
                run_id=run_id, event=event, expected_state_version=run.state_version
            )
            actions.append("effect_reconciled_close" if apply.accepted else f"close_rejected:{apply.reason}")
            run = self.runtime.get_run(run_id)
            return ReconcileResult(
                run_id=run_id,
                actions=actions,
                run=run.to_dict(),
                closed=bool(run.closed),
                reason=apply.reason,
            )

        return ReconcileResult(run_id=run_id, actions=actions, run=run.to_dict())
