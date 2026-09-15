"""Durable Effect Journal with crash-safe GitHub PR mutations.

Lifecycle:
  declared → prepared → executing → succeeded|failed|ambiguous

Crash windows:
  - before execute: retry from declared/prepared
  - after remote mutate, before local commit: status=executing → reconcile via observation
  - ambiguous remote outcome: status=ambiguous; fail closed until reconcile
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Optional

from .durable_models import Effect
from .effect_allowlist import assert_effect_allowed
from .github_mutate import GitHubMutator, MutationError


def _utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def effect_identity(
    *,
    run_id: str,
    action: str,
    repo: str,
    target: str,
    head_sha: str,
) -> str:
    material = "|".join([run_id, action, repo, target, head_sha])
    digest = hashlib.sha256(material.encode("utf-8")).hexdigest()[:16]
    # Avoid generic-api-key false positives from bare high-entropy tokens.
    return f"effect/{action}/{digest}"


class DurableEffectJournal:
    """SQLite-backed journal; mutator injected (fake or gh)."""

    def __init__(self, store: Any, mutator: GitHubMutator) -> None:
        self.store = store
        self.mutator = mutator

    def declare(
        self,
        *,
        run_id: str,
        action: str,
        repo: str,
        target: str,
        head_sha: str,
        approval_id: Optional[str] = None,
    ) -> Effect:
        assert_effect_allowed(action=action, repo=repo)
        eid = effect_identity(
            run_id=run_id, action=action, repo=repo, target=target, head_sha=head_sha
        )
        existing = self.store.get_effect(eid)
        if existing is not None:
            return existing
        now = _utcnow()
        rec = Effect(
            effect_id=eid,
            run_id=run_id,
            action=action,
            repo=repo,
            target=target,
            head_sha=head_sha,
            created_at=now,
            status="declared",
            approval_id=approval_id,
            idempotency_key=eid,
        )
        self.store.insert_effect(rec)
        return rec

    def prepare(self, effect_id: str, *, precheck: dict[str, Any]) -> Effect:
        rec = self.store.get_effect(effect_id)
        if rec is None:
            raise KeyError(effect_id)
        if rec.status == "succeeded":
            return rec
        if rec.status == "ambiguous":
            raise RuntimeError("effect ambiguous; reconcile before prepare")
        now = _utcnow()
        rec.status = "prepared"
        rec.prepared_at = now
        rec.result_json = json.dumps({"precheck": precheck}, sort_keys=True)
        self.store.update_effect(rec)
        return rec

    def begin_execute(self, effect_id: str) -> Effect:
        rec = self.store.get_effect(effect_id)
        if rec is None:
            raise KeyError(effect_id)
        if rec.status == "succeeded":
            return rec
        if rec.status not in ("prepared", "executing", "declared"):
            raise RuntimeError(f"cannot execute from status={rec.status}")
        now = _utcnow()
        rec.status = "executing"
        rec.executing_at = now
        self.store.update_effect(rec)
        return rec

    def execute(self, effect_id: str, *, params: Optional[dict[str, Any]] = None) -> Effect:
        params = params or {}
        rec = self.store.get_effect(effect_id)
        if rec is None:
            raise KeyError(effect_id)
        if rec.status == "succeeded":
            return rec
        if rec.status == "ambiguous":
            raise RuntimeError("effect ambiguous; reconcile required")
        assert_effect_allowed(action=rec.action, repo=rec.repo)
        rec = self.begin_execute(effect_id)
        try:
            result = self._dispatch(rec, params)
            rec.status = "succeeded"
            rec.finished_at = _utcnow()
            rec.external_ref = str(
                result.get("url") or result.get("number") or rec.external_ref or rec.target
            )
            rec.result_json = json.dumps(result, sort_keys=True)
            rec.error = None
            self.store.update_effect(rec)
            return rec
        except MutationError as exc:
            msg = str(exc)
            if any(tok in msg.lower() for tok in ("502", "503", "timeout", "ambiguous", "unknown")):
                rec.status = "ambiguous"
                rec.error = msg
                rec.finished_at = _utcnow()
                self.store.update_effect(rec)
                raise
            rec.status = "failed"
            rec.error = msg
            rec.finished_at = _utcnow()
            self.store.update_effect(rec)
            raise

    def mark_reconciled_success(self, effect_id: str, *, evidence: dict[str, Any]) -> Effect:
        rec = self.store.get_effect(effect_id)
        if rec is None:
            raise KeyError(effect_id)
        rec.status = "succeeded"
        rec.finished_at = _utcnow()
        rec.error = None
        rec.result_json = json.dumps({"reconciled": evidence}, sort_keys=True)
        self.store.update_effect(rec)
        return rec

    def _dispatch(self, rec: Effect, params: dict[str, Any]) -> dict[str, Any]:
        if rec.action == "github_pr_comment":
            pr = int(params.get("pr_number") or str(rec.target).split("/")[-1])
            body = str(params.get("body") or "graph-control-plane effect")
            return self.mutator.pr_comment(repo=rec.repo, pr_number=pr, body=body)
        if rec.action == "github_pr_merge":
            pr = int(params.get("pr_number") or str(rec.target).split("/")[-1])
            method = str(params.get("method") or "squash")
            return self.mutator.pr_merge(repo=rec.repo, pr_number=pr, method=method)
        if rec.action == "github_pr_create":
            return self.mutator.pr_create(
                repo=rec.repo,
                title=str(params["title"]),
                body=str(params.get("body") or ""),
                head=str(params.get("head") or rec.target),
                base=str(params.get("base") or "main"),
            )
        raise MutationError(f"unsupported action {rec.action}")
