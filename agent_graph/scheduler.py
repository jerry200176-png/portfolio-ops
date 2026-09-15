"""Bounded scheduler: single-tick and autonomous single-host loop.

Advances runnable Runs by deterministic graph state — never invents policy.
"""

from __future__ import annotations

import json
import os
import signal
import subprocess
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Optional

from .durable_runtime import DurableGraphRuntime
from .github_mutate import GhCliMutator, GitHubMutator
from .harness import FakeWorkerAdapter, GraphHarness
from .observation import ci_authorizes_head
from .policy_gate import advance_human_gate_by_policy
from .reconciler import GraphReconciler
from .risk_policy import requires_founder_approval
from .scheduler_ownership import SchedulerOwnership


def _utcnow() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass
class ScheduleTickResult:
    examined: int
    advanced: list[dict[str, Any]]
    idle: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "examined": self.examined,
            "advanced": self.advanced,
            "idle": self.idle,
        }


@dataclass
class SchedulerStatus:
    scheduler_id: str
    started_at: str
    last_tick_at: Optional[str] = None
    last_error: Optional[str] = None
    ticks: int = 0
    ownership_held: bool = False
    poll_interval_sec: float = 2.0
    shutting_down: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "scheduler_id": self.scheduler_id,
            "started_at": self.started_at,
            "last_tick_at": self.last_tick_at,
            "last_error": self.last_error,
            "ticks": self.ticks,
            "ownership_held": self.ownership_held,
            "poll_interval_sec": self.poll_interval_sec,
            "shutting_down": self.shutting_down,
            "uptime_sec": (
                datetime.fromisoformat(_utcnow().replace("Z", "+00:00"))
                - datetime.fromisoformat(self.started_at.replace("Z", "+00:00"))
            ).total_seconds()
            if self.started_at
            else 0,
        }


def _effect_pr_number(effects: list[Any]) -> Optional[int]:
    for eff in reversed(effects):
        if eff.action == "github_pr_create" and eff.status == "succeeded":
            try:
                data = json.loads(eff.result_json or "{}")
                num = data.get("number")
                if num is not None:
                    return int(num)
            except (json.JSONDecodeError, TypeError, ValueError):
                pass
        target = getattr(eff, "target", "") or ""
        if target.startswith("pr/") and eff.status == "succeeded":
            try:
                return int(target.split("/", 1)[1])
            except (IndexError, ValueError):
                pass
    return None


def _observation_pr_number(run: Any) -> Optional[int]:
    obs = (run.graph_snapshot or {}).get("observations") or {}
    for fact in obs.get("facts") or []:
        ext = fact.get("external_ref") or ""
        if "#pr/" in ext:
            try:
                return int(ext.rsplit("#pr/", 1)[1])
            except (IndexError, ValueError):
                pass
        raw = fact.get("raw") or {}
        if raw.get("number") is not None:
            try:
                return int(raw["number"])
            except (TypeError, ValueError):
                pass
    latest = obs.get("latest_by_type") or {}
    for key in latest:
        ext = (latest[key] or {}).get("external_ref") or ""
        if "#pr/" in ext:
            try:
                return int(ext.rsplit("#pr/", 1)[1])
            except (IndexError, ValueError):
                pass
    return None


def _find_pr_by_branch(repo: str, branch: str) -> Optional[int]:
    if not branch:
        return None
    try:
        proc = subprocess.run(
            [
                "gh",
                "pr",
                "list",
                "--repo",
                repo,
                "--head",
                branch,
                "--json",
                "number",
                "--limit",
                "1",
            ],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        if proc.returncode != 0:
            return None
        rows = json.loads(proc.stdout or "[]")
        if rows:
            return int(rows[0]["number"])
    except (subprocess.TimeoutExpired, json.JSONDecodeError, KeyError, ValueError, OSError):
        return None
    return None


class GraphScheduler:
    def __init__(
        self,
        runtime: DurableGraphRuntime,
        *,
        reconciler: Optional[GraphReconciler] = None,
        mutator: Optional[GitHubMutator] = None,
        head_sha: str = "c" * 40,
        use_real_codex: bool = False,
        codex_timeout_sec: float = 900.0,
        canonical_db_path: Optional[str] = None,
    ) -> None:
        self.runtime = runtime
        self.reconciler = reconciler
        self.mutator = mutator or GhCliMutator()
        self.head_sha = head_sha
        self.use_real_codex = use_real_codex
        self.codex_timeout_sec = codex_timeout_sec
        self.canonical_db_path = canonical_db_path
        self.harness = GraphHarness(runtime)

    def _worker_for_run(self, run: Any) -> Any:
        if self.use_real_codex and run.current_node in ("investigator", "builder"):
            from .real_codex_adapter import RealCodexWorkerAdapter

            return RealCodexWorkerAdapter(
                timeout_sec=self.codex_timeout_sec,
                ephemeral=True,
                canonical_db_path=self.canonical_db_path,
            )
        return FakeWorkerAdapter(head_sha=run.head_sha or self.head_sha)

    def list_runnable(self, limit: int = 20) -> list[str]:
        rows = self.runtime.store._conn.execute(
            """
            SELECT run_id FROM runs
            WHERE closed=0 AND stopped=0
              AND status IN (
                'running','waiting_worker','waiting_for_approval','approved_for_effect'
              )
            ORDER BY updated_at ASC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [r["run_id"] for r in rows]

    def _advance_approved_for_effect(
        self,
        run_id: str,
        *,
        pr_number: Optional[int] = None,
    ) -> dict[str, Any]:
        run = self.runtime.get_run(run_id)
        repo = f"jerry200176-png/{run.project}"
        effects = self.runtime.store.list_effects(run_id)
        pr_num = pr_number or _effect_pr_number(effects) or _observation_pr_number(run)
        if pr_num is None and run.branch:
            pr_num = _find_pr_by_branch(repo, run.branch)

        actions: list[str] = []

        create_done = any(
            e.action == "github_pr_create" and e.status == "succeeded" for e in effects
        )
        merge_done = any(
            e.action == "github_pr_merge" and e.status == "succeeded" for e in effects
        )
        merge_ambiguous = any(
            e.action == "github_pr_merge" and e.status == "ambiguous" for e in effects
        )

        if not create_done and not pr_num and run.branch and run.head_sha:
            # Re-publish branch tip before PR create (builder push may have failed).
            if self.use_real_codex and run.worktree:
                from .branch_push import BranchPushError, try_ensure_branch_pushed

                try:
                    push_meta = try_ensure_branch_pushed(run.worktree)
                    actions.append("branch_push_before_pr")
                except BranchPushError as exc:
                    return {
                        "run_id": run_id,
                        "action": "branch_push_failed",
                        "blocker": "branch_push_failed",
                        "error": str(exc),
                        "actions": actions,
                    }
            else:
                push_meta = None

            title = f"graph run {run_id}: {run.branch}"
            body = (
                f"Autonomous graph control-plane PR for run `{run_id}`.\n\n"
                f"Head SHA: `{run.head_sha}`"
            )
            out = self.runtime.execute_approved_effect(
                run_id=run_id,
                action="github_pr_create",
                repo=repo,
                target=f"branch/{run.branch}",
                mutator=self.mutator,
                params={
                    "title": title,
                    "body": body,
                    "head": run.branch,
                    "base": "main",
                },
                observed_head_sha=run.head_sha,
            )
            actions.append("pr_create")
            if push_meta is not None:
                actions.append(
                    "branch_push:"
                    + ("up_to_date" if push_meta.get("already_up_to_date") else "pushed")
                )
            if out.get("accepted"):
                try:
                    pr_num = int(json.loads(out["effect"]["result_json"])["number"])
                except (KeyError, TypeError, json.JSONDecodeError, ValueError):
                    pass
            elif out.get("blocker") == "stale_approval":
                return {"run_id": run_id, "action": "effect_blocked", "result": out}
            else:
                return {"run_id": run_id, "action": "pr_create_failed", "result": out}

        if self.reconciler is not None and pr_num is not None:
            rec = self.reconciler.reconcile_run(run_id, pr_number=pr_num, repo=repo)
            actions.append("reconcile_observe")
            run = self.runtime.get_run(run_id)
            if run.closed:
                return {
                    "run_id": run_id,
                    "action": "reconcile_closed",
                    "pr_number": pr_num,
                    "result": rec.to_dict(),
                }

        if merge_ambiguous and self.reconciler is not None and pr_num is not None:
            rec = self.reconciler.reconcile_run(run_id, pr_number=pr_num, repo=repo)
            run = self.runtime.get_run(run_id)
            return {
                "run_id": run_id,
                "action": "reconcile_ambiguous_merge",
                "pr_number": pr_num,
                "result": rec.to_dict(),
                "closed": run.closed,
            }

        run = self.runtime.get_run(run_id)
        obs = (run.graph_snapshot or {}).get("observations") or {}
        ci_ok = ci_authorizes_head(obs, run.head_sha or "")

        if not merge_done and pr_num is not None and not ci_ok:
            ci_state = (obs.get("ci_by_sha") or {}).get(run.head_sha or "")
            if ci_state == "CI_FAILED":
                return {
                    "run_id": run_id,
                    "action": "ci_failed",
                    "blocker": "ci_failed",
                    "pr_number": pr_num,
                    "ci_state": ci_state,
                    "actions": actions,
                }
            return {
                "run_id": run_id,
                "action": "wait_ci",
                "pr_number": pr_num,
                "actions": actions,
                "ci_ok": False,
            }

        if not merge_done and pr_num is not None and ci_ok and run.head_sha:
            out = self.runtime.execute_approved_effect(
                run_id=run_id,
                action="github_pr_merge",
                repo=repo,
                target=f"pr/{pr_num}",
                mutator=self.mutator,
                params={"pr_number": pr_num},
                require_ci=True,
                observed_head_sha=run.head_sha,
            )
            actions.append("pr_merge")
            if out.get("accepted") and self.reconciler is not None:
                rec = self.reconciler.reconcile_run(run_id, pr_number=pr_num, repo=repo)
                run = self.runtime.get_run(run_id)
                return {
                    "run_id": run_id,
                    "action": "merge_and_reconcile",
                    "pr_number": pr_num,
                    "merge": out,
                    "reconcile": rec.to_dict(),
                    "closed": run.closed,
                }
            if out.get("blocker") == "ci_not_green":
                return {
                    "run_id": run_id,
                    "action": "wait_ci",
                    "pr_number": pr_num,
                    "result": out,
                }
            return {
                "run_id": run_id,
                "action": "merge_attempt",
                "pr_number": pr_num,
                "result": out,
            }

        if self.reconciler is not None and pr_num is not None:
            rec = self.reconciler.reconcile_run(run_id, pr_number=pr_num, repo=repo)
            run = self.runtime.get_run(run_id)
            return {
                "run_id": run_id,
                "action": "reconcile_only",
                "pr_number": pr_num,
                "result": rec.to_dict(),
                "closed": run.closed,
                "actions": actions,
            }

        return {
            "run_id": run_id,
            "action": "wait_effect",
            "pr_number": pr_num,
            "actions": actions,
        }

    def tick(
        self,
        *,
        limit: int = 5,
        pr_number: Optional[int] = None,
        skip_run_ids: Optional[set[str]] = None,
    ) -> ScheduleTickResult:
        advanced: list[dict[str, Any]] = []
        skip = skip_run_ids or set()
        ids = [rid for rid in self.list_runnable(limit=limit * 2) if rid not in skip][:limit]
        if not ids:
            return ScheduleTickResult(examined=0, advanced=[], idle=True)

        for run_id in ids:
            run = self.runtime.get_run(run_id)
            if run.status == "waiting_for_approval":
                if requires_founder_approval(run.risk_tier):
                    advanced.append(
                        {"run_id": run_id, "action": "dormant_waiting_for_approval"}
                    )
                    continue
                out = advance_human_gate_by_policy(self.runtime, run_id)
                advanced.append(
                    {
                        "run_id": run_id,
                        "action": "policy_advance_human_gate",
                        "accepted": out.get("accepted"),
                        "result": out,
                    }
                )
                continue
            if run.current_node == "approved_for_effect":
                try:
                    item = self._advance_approved_for_effect(run_id, pr_number=pr_number)
                    advanced.append(item)
                except Exception as exc:  # noqa: BLE001 — transient observe failures
                    advanced.append(
                        {
                            "run_id": run_id,
                            "action": "observe_error",
                            "error": str(exc),
                            "transient": True,
                        }
                    )
                continue
            if run.current_node in ("investigator", "builder", "reviewer"):
                try:
                    node_before = run.current_node
                    worker = self._worker_for_run(run)
                    stepped = self.harness.step(
                        run_id,
                        worker=worker,
                        model_profile="codex-route" if self.use_real_codex else None,
                        write_context=True,
                    )
                    entry: dict[str, Any] = {
                        "run_id": run_id,
                        "action": "step",
                        "accepted": stepped.apply.accepted,
                        "node": stepped.apply.run.current_node,
                        "worker_type": getattr(worker, "worker_type", "unknown"),
                        "node_before": node_before,
                    }
                    launch = getattr(worker, "last_launch", None)
                    if launch is not None:
                        entry["worker_pid"] = launch.pid
                        entry["codex_launch"] = launch.to_dict()
                        if getattr(launch, "failure_reason", None) == "codex_usage_limit":
                            entry["action"] = "dormant_codex_usage_limit"
                            entry["blocker"] = "codex_usage_limit"
                    # Control plane publishes the branch after RealCodex builder
                    # commits so PR create does not depend on Codex sandbox network.
                    if (
                        self.use_real_codex
                        and node_before == "builder"
                        and stepped.apply.accepted
                        and entry.get("action") == "step"
                    ):
                        from .branch_push import BranchPushError, try_ensure_branch_pushed

                        wt = stepped.apply.run.worktree or run.worktree
                        try:
                            entry["branch_push"] = try_ensure_branch_pushed(wt)
                        except BranchPushError as exc:
                            entry["action"] = "branch_push_failed"
                            entry["blocker"] = "branch_push_failed"
                            entry["error"] = str(exc)
                    advanced.append(entry)
                except Exception as exc:  # noqa: BLE001 — tick must continue
                    advanced.append(
                        {"run_id": run_id, "action": "step_error", "error": str(exc)}
                    )
                continue
            advanced.append({"run_id": run_id, "action": "noop", "node": run.current_node})

        # Dormancy and external waits (CI / effect journal) count as idle for backoff —
        # spinning every poll_interval burns CPU without progress.
        wait_actions = frozenset(
            {
                "wait_ci",
                "wait_effect",
                "observe_error",
                "dormant_codex_usage_limit",
                "dormant_no_worker",
                "dormant_no_github",
            }
        )
        only_waiting = bool(advanced) and all(
            a.get("action") in wait_actions
            or str(a.get("action", "")).startswith("dormant_")
            for a in advanced
        )
        return ScheduleTickResult(
            examined=len(ids),
            advanced=advanced,
            idle=(not advanced) or only_waiting,
        )


class AutonomousSchedulerLoop:
    """Single-host bounded poll loop with exclusive scheduler ownership."""

    def __init__(
        self,
        runtime: DurableGraphRuntime,
        *,
        reconciler: Optional[GraphReconciler] = None,
        mutator: Optional[GitHubMutator] = None,
        project: str = "portfolio-ops",
        poll_interval_sec: float = 2.0,
        max_poll_interval_sec: float = 30.0,
        lease_ttl_sec: float = 30.0,
        tick_limit: int = 5,
        use_real_codex: bool = False,
        codex_timeout_sec: float = 900.0,
        canonical_db_path: Optional[str] = None,
        scheduler_id: Optional[str] = None,
        sleep_fn: Callable[[float], None] = time.sleep,
    ) -> None:
        self.runtime = runtime
        self.project = project
        self.poll_interval_sec = poll_interval_sec
        self.max_poll_interval_sec = max_poll_interval_sec
        self.lease_ttl_sec = float(lease_ttl_sec)
        self.tick_limit = tick_limit
        self.sleep_fn = sleep_fn
        self.scheduler_id = scheduler_id or f"schedloop_{uuid.uuid4().hex[:12]}"
        self.ownership = SchedulerOwnership(
            store=runtime.store,
            project=project,
            owner_id=self.scheduler_id,
            ttl_sec=lease_ttl_sec,
        )
        self.scheduler = GraphScheduler(
            runtime,
            reconciler=reconciler,
            mutator=mutator,
            use_real_codex=use_real_codex,
            codex_timeout_sec=codex_timeout_sec,
            canonical_db_path=canonical_db_path,
        )
        self.status = SchedulerStatus(
            scheduler_id=self.scheduler_id,
            started_at=_utcnow(),
            poll_interval_sec=poll_interval_sec,
        )
        self._stop_requested = False
        self._current_interval = poll_interval_sec
        self._permanent_blockers: set[str] = set()
        # run_id -> unix epoch when Codex quota dormancy lifts (not permanent).
        self._codex_dormant_until: dict[str, float] = {}
        self.focus_run_ids: Optional[set[str]] = None

    def request_stop(self) -> None:
        self._stop_requested = True
        self.status.shutting_down = True

    def install_signal_handlers(self) -> None:
        def _on_term(_signum: int, _frame: Any) -> None:
            self.request_stop()

        signal.signal(signal.SIGTERM, _on_term)
        signal.signal(signal.SIGINT, _on_term)

    def acquire_ownership(self) -> bool:
        ok = self.ownership.try_acquire()
        self.status.ownership_held = ok
        return ok

    def release_ownership(self) -> None:
        self.ownership.release()
        self.status.ownership_held = False

    def _active_codex_dormant_skips(self, *, now: Optional[float] = None) -> set[str]:
        ts = time.time() if now is None else now
        expired = [rid for rid, until in self._codex_dormant_until.items() if until <= ts]
        for rid in expired:
            self._codex_dormant_until.pop(rid, None)
        return set(self._codex_dormant_until.keys())

    def _record_blockers(self, tick: ScheduleTickResult) -> None:
        for item in tick.advanced:
            blocker = item.get("blocker") or (item.get("result") or {}).get("blocker")
            rid = item.get("run_id")
            if not rid:
                continue
            if blocker in ("founder_approval_required", "ci_failed"):
                self._permanent_blockers.add(rid)
            # stale_approval is recoverable after head re-observe / re-approve — do not
            # permanently skip the Run in a long-lived schedule-run process.
            if item.get("action") == "ci_failed":
                self._permanent_blockers.add(rid)
            if item.get("action") == "dormant_codex_usage_limit" or blocker == "codex_usage_limit":
                resume = None
                launch = item.get("codex_launch") or {}
                if isinstance(launch, dict):
                    resume = launch.get("usage_resume_epoch")
                if resume is None:
                    env_epoch = os.environ.get("GRAPH_CODEX_QUOTA_RESUME_EPOCH")
                    if env_epoch:
                        try:
                            resume = float(env_epoch)
                        except ValueError:
                            resume = None
                if resume is None:
                    # Default: skip for 6h rather than forever (long-lived schedule-run).
                    resume = time.time() + 6 * 3600
                self._codex_dormant_until[rid] = float(resume)

    def _next_sleep(self, tick: ScheduleTickResult) -> float:
        if tick.idle:
            self._current_interval = min(
                self.max_poll_interval_sec, self._current_interval * 1.5
            )
            # If only waiting on Codex quota, sleep toward the earliest resume
            # (capped) so the loop resumes without process restart.
            if self._codex_dormant_until:
                soonest = min(self._codex_dormant_until.values()) - time.time()
                if soonest > 0:
                    self._current_interval = min(
                        max(self._current_interval, soonest),
                        max(self.max_poll_interval_sec, min(soonest, 6 * 3600)),
                    )
        else:
            self._current_interval = self.poll_interval_sec
        return self._current_interval

    def tick_once(self) -> ScheduleTickResult:
        if self.status.ownership_held:
            self.ownership.renew()
        skip = set(self._permanent_blockers) | self._active_codex_dormant_skips()
        if self.focus_run_ids is not None:
            # Skip everything outside the focused dogfood/ops set.
            runnable = self.scheduler.list_runnable(limit=200)
            skip |= {rid for rid in runnable if rid not in self.focus_run_ids}
        tick = self.scheduler.tick(limit=self.tick_limit, skip_run_ids=skip)
        self.status.last_tick_at = _utcnow()
        self.status.ticks += 1
        self._record_blockers(tick)
        return tick

    def run_forever(self, *, max_ticks: Optional[int] = None) -> int:
        if not self.acquire_ownership():
            self.status.last_error = "scheduler ownership not acquired"
            return 2
        ticks_run = 0
        try:
            while not self._stop_requested:
                if max_ticks is not None and ticks_run >= max_ticks:
                    break
                tick = self.tick_once()
                ticks_run += 1
                sleep_for = self._next_sleep(tick)
                self.status.poll_interval_sec = sleep_for
                if self._stop_requested:
                    break
                self.sleep_fn(sleep_for)
            return 0
        except Exception as exc:  # noqa: BLE001
            self.status.last_error = str(exc)
            return 1
        finally:
            self.release_ownership()

    def operational_snapshot(self) -> dict[str, Any]:
        runnable = self.scheduler.list_runnable(limit=50)
        blocked = []
        active = []
        for run_id in runnable:
            run = self.runtime.get_run(run_id)
            if run.status == "waiting_for_approval" and requires_founder_approval(
                run.risk_tier
            ):
                blocked.append(run.to_dict())
            elif run_id in self._permanent_blockers or run_id in self._codex_dormant_until:
                blocked.append(run.to_dict())
            else:
                active.append(run.to_dict())
        return {
            "scheduler": self.status.to_dict(),
            "ownership": self.ownership.status(),
            "active_runs": active,
            "blocked_runs": blocked,
            "runnable_count": len(runnable),
            "codex_dormant_until": dict(self._codex_dormant_until),
        }
