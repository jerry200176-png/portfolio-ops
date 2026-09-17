"""Minimal CLI for durable Graph Control Plane (Phase 1A–1C).

Commands:
  run-create | status | step | events | resume | bind-worktree | observe | approve
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .canonical_paths import default_canonical_db_path, ensure_canonical_db_parent
from .durable_runtime import DurableGraphRuntime
from .github_observe import FakeGitHubReader, GhCliReader, observe_pull_request
from .github_mutate import FakeGitHubMutator, GhCliMutator
from .reconciler import GraphReconciler
from .scheduler import AutonomousSchedulerLoop, GraphScheduler
from .harness import FakeWorkerAdapter, GraphHarness
from .sqlite_store import SqliteControlPlaneStore
from .worktree_bind import bind_existing_worktree

DEFAULT_DB = default_canonical_db_path()


def _runtime(db: str) -> DurableGraphRuntime:
    path = ensure_canonical_db_parent(Path(db))
    return DurableGraphRuntime(SqliteControlPlaneStore(path))


def cmd_run_create(args: argparse.Namespace) -> int:
    rt = _runtime(args.db)
    try:
        run = rt.create_run(
            objective=args.objective,
            project=args.project,
            risk_tier=args.risk_tier,
            success_condition=args.success_condition,
            repository=args.repository,
            base_sha=args.base_sha,
            worktree=args.worktree,
            branch=args.branch,
        )
        print(json.dumps(run.to_dict(), indent=2, sort_keys=True))
        return 0
    finally:
        rt.close()


def cmd_status(args: argparse.Namespace) -> int:
    rt = _runtime(args.db)
    try:
        run = rt.get_run(args.run_id)
        print(json.dumps(run.to_dict(), indent=2, sort_keys=True))
        return 0
    finally:
        rt.close()


def cmd_events(args: argparse.Namespace) -> int:
    rt = _runtime(args.db)
    try:
        events = [e.to_dict() for e in rt.list_events(args.run_id)]
        print(json.dumps(events, indent=2, sort_keys=True))
        return 0
    finally:
        rt.close()


def cmd_step(args: argparse.Namespace) -> int:
    rt = _runtime(args.db)
    try:
        harness = GraphHarness(rt)
        if args.codex_worker:
            from .real_codex_adapter import RealCodexWorkerAdapter

            worker = RealCodexWorkerAdapter(
                timeout_sec=args.codex_timeout,
                dry_run=args.codex_dry_run,
                canonical_db_path=args.db,
            )
            model_profile = "codex-route"
        elif getattr(args, "external_cli_worker", False):
            from .external_cli_adapter import ExternalCliWorkerAdapter

            worker = ExternalCliWorkerAdapter(
                provider_id=args.external_cli_provider,
                timeout_sec=args.external_cli_timeout,
                dry_run=args.external_cli_dry_run,
                canonical_db_path=args.db,
            )
            model_profile = f"external_cli:{args.external_cli_provider}"
        else:
            worker = FakeWorkerAdapter(head_sha=args.head_sha)
            model_profile = None
        result = harness.step(
            args.run_id,
            worker=worker,
            model_profile=model_profile,
            write_context=not args.no_context,
        )
        payload = result.to_dict()
        launch = getattr(worker, "last_launch", None)
        if launch is not None:
            payload["worker_launch"] = launch.to_dict()
            # Back-compat key for existing Codex consumers.
            if getattr(worker, "worker_type", "") == "codex":
                payload["codex_launch"] = launch.to_dict()
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0 if result.apply.accepted or result.duplicate_ingest else 1
    finally:
        rt.close()


def cmd_resume(args: argparse.Namespace) -> int:
    """Reload Run from SQLite and optionally execute the next node.

    Proves process identity is irrelevant: a brand-new runtime continues.
    """
    rt = _runtime(args.db)
    try:
        run = rt.get_run(args.run_id)
        payload = {
            "resumed": True,
            "run": run.to_dict(),
            "event_count": len(rt.list_events(args.run_id)),
        }
        if args.step:
            harness = GraphHarness(rt)
            stepped = harness.step(args.run_id, worker=FakeWorkerAdapter(head_sha=args.head_sha))
            payload["step"] = stepped.to_dict()
            print(json.dumps(payload, indent=2, sort_keys=True))
            return 0 if stepped.apply.accepted or stepped.duplicate_ingest else 1
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0
    finally:
        rt.close()


def cmd_bind_worktree(args: argparse.Namespace) -> int:
    rt = _runtime(args.db)
    try:
        out = bind_existing_worktree(
            rt,
            args.run_id,
            worktree=args.worktree,
            branch=args.branch,
            base_sha=args.base_sha,
        )
        print(json.dumps(out, indent=2, sort_keys=True))
        return 0
    finally:
        rt.close()


def cmd_observe(args: argparse.Namespace) -> int:
    """Manual read-only external observation: graph observe RUN_ID --pr N."""
    rt = _runtime(args.db)
    try:
        run = rt.get_run(args.run_id)
        repo = args.repo or f"jerry200176-png/{run.project}"
        if args.fixture_json:
            reader = FakeGitHubReader(json.loads(Path(args.fixture_json).read_text(encoding="utf-8")))
        else:
            reader = GhCliReader()
        facts = observe_pull_request(repo=repo, pr_number=int(args.pr), reader=reader)
        results = []
        for fact in facts:
            out = rt.ingest_observation(run_id=args.run_id, fact=fact, repository=repo)
            results.append(
                {
                    "fact": fact.to_dict(),
                    "accepted": out.accepted,
                    "duplicate": out.duplicate,
                    "reason": out.reason,
                    "blocker": out.blocker,
                    "event_id": out.event.event_id if out.event else None,
                }
            )
        run2 = rt.get_run(args.run_id)
        print(
            json.dumps(
                {"observations": results, "run": run2.to_dict()},
                indent=2,
                sort_keys=True,
            )
        )
        return 0 if all(r["accepted"] or r["duplicate"] for r in results) else 1
    finally:
        rt.close()


def cmd_approve(args: argparse.Namespace) -> int:
    """Trusted Founder Approval path: graph approve RUN_ID --action ... --head-sha ..."""
    rt = _runtime(args.db)
    try:
        out = rt.grant_founder_approval(
            run_id=args.run_id,
            action=args.action,
            head_sha=args.head_sha,
            actor=args.actor,
            scope=args.scope,
            external_ref=args.external_ref,
            expires_at=args.expires_at,
        )
        print(json.dumps(out, indent=2, sort_keys=True))
        return 0 if out.get("accepted") else 1
    finally:
        rt.close()




def cmd_effect(args: argparse.Namespace) -> int:
    """Execute allowlisted effect (no production deploy)."""
    rt = _runtime(args.db)
    try:
        mutator = FakeGitHubMutator() if args.fake else GhCliMutator()
        params = {}
        if args.pr is not None:
            params["pr_number"] = int(args.pr)
        if args.body:
            params["body"] = args.body
        if args.title:
            params["title"] = args.title
        if args.head:
            params["head"] = args.head
        out = rt.execute_approved_effect(
            run_id=args.run_id,
            action=args.action,
            repo=args.repo,
            target=args.target or (f"pr/{args.pr}" if args.pr else "unknown"),
            mutator=mutator,
            params=params,
            require_ci=args.require_ci,
            observed_head_sha=args.observed_head_sha,
        )
        print(json.dumps(out, indent=2, sort_keys=True))
        return 0 if out.get("accepted") else 1
    finally:
        rt.close()


def cmd_reconcile(args: argparse.Namespace) -> int:
    rt = _runtime(args.db)
    try:
        reader = FakeGitHubReader(json.loads(Path(args.fixture_json).read_text(encoding="utf-8"))) if args.fixture_json else GhCliReader()
        rec = GraphReconciler(rt, reader)
        out = rec.reconcile_run(args.run_id, pr_number=args.pr, repo=args.repo)
        print(json.dumps(out.to_dict(), indent=2, sort_keys=True))
        return 0
    finally:
        rt.close()


def cmd_schedule_tick(args: argparse.Namespace) -> int:
    rt = _runtime(args.db)
    try:
        reader = GhCliReader()
        rec = GraphReconciler(rt, reader)
        mutator = FakeGitHubMutator() if args.fake else GhCliMutator()
        sched = GraphScheduler(
            rt,
            reconciler=rec,
            mutator=mutator,
            head_sha=args.head_sha,
            use_real_codex=args.real_codex,
            codex_timeout_sec=args.codex_timeout,
            canonical_db_path=args.db,
        )
        out = sched.tick(limit=args.limit, pr_number=args.pr)
        print(json.dumps(out.to_dict(), indent=2, sort_keys=True))
        return 0
    finally:
        rt.close()


def cmd_schedule_run(args: argparse.Namespace) -> int:
    rt = _runtime(args.db)
    try:
        reader = GhCliReader()
        rec = GraphReconciler(rt, reader)
        mutator = FakeGitHubMutator() if args.fake else GhCliMutator()
        loop = AutonomousSchedulerLoop(
            rt,
            reconciler=rec,
            mutator=mutator,
            project=args.project,
            poll_interval_sec=args.poll_interval,
            max_poll_interval_sec=args.max_poll_interval,
            lease_ttl_sec=args.lease_ttl,
            tick_limit=args.limit,
            use_real_codex=args.real_codex,
            codex_timeout_sec=args.codex_timeout,
            canonical_db_path=args.db,
        )
        if not args.no_signals:
            loop.install_signal_handlers()
        if args.max_ticks is not None:
            code = loop.run_forever(max_ticks=args.max_ticks)
        else:
            code = loop.run_forever()
        print(json.dumps(loop.operational_snapshot(), indent=2, sort_keys=True))
        return code
    finally:
        rt.close()


def cmd_schedule_status(args: argparse.Namespace) -> int:
    rt = _runtime(args.db)
    try:
        from .scheduler_ownership import SchedulerOwnership
        from .risk_policy import requires_founder_approval

        ownership = SchedulerOwnership(store=rt.store, project=args.project)
        sched = GraphScheduler(rt)
        runnable = sched.list_runnable(limit=50)
        active: list[dict] = []
        blocked: list[dict] = []
        for rid in runnable:
            run = rt.get_run(rid)
            row = {
                "run_id": rid,
                "status": run.status,
                "current_node": run.current_node,
                "blocker": run.blocker,
                "risk_tier": run.risk_tier,
                "updated_at": run.updated_at,
            }
            if run.status == "waiting_for_approval" and requires_founder_approval(
                run.risk_tier
            ):
                blocked.append(row)
            elif run.blocker:
                blocked.append(row)
            else:
                active.append(row)
        # Lease / identity from ownership status (includes owner_id, expires).
        own = ownership.status()
        payload = {
            "scheduler_identity": own.get("owner_id") or own.get("holder"),
            "ownership": own,
            "runnable_count": len(runnable),
            "active_runs": active,
            "blocked_runs": blocked,
            "runnable_run_ids": runnable,
            "control_db": args.db,
            "project": args.project,
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0
    finally:
        rt.close()


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="graph", description="Durable Graph Control Plane CLI (Phase 1A–1C)"
    )
    p.add_argument(
        "--db",
        default=str(DEFAULT_DB),
        help="Path to control-plane SQLite DB (gitignored)",
    )
    sub = p.add_subparsers(dest="command", required=True)

    c = sub.add_parser("run-create", help="Create Goal + Run and commit TASK_CREATED")
    c.add_argument("--objective", required=True)
    c.add_argument("--project", default="portfolio-ops")
    c.add_argument("--risk-tier", default="low")
    c.add_argument("--success-condition", default=None)
    c.add_argument("--repository", default="jerry200176-png/portfolio-ops")
    c.add_argument("--base-sha", default=None)
    c.add_argument("--worktree", default=None)
    c.add_argument("--branch", default=None)
    c.set_defaults(func=cmd_run_create)

    c = sub.add_parser("status", help="Show canonical Run projection from SQLite")
    c.add_argument("run_id")
    c.set_defaults(func=cmd_status)

    c = sub.add_parser("events", help="Show append-only event history")
    c.add_argument("run_id")
    c.set_defaults(func=cmd_events)

    c = sub.add_parser("step", help="Start attempt, run worker adapter, ingest result")
    c.add_argument("run_id")
    c.add_argument("--fake-worker", action="store_true", default=True)
    c.add_argument(
        "--codex-worker",
        action="store_true",
        help="Use RealCodexWorkerAdapter via codex-route (replaceable worker)",
    )
    c.add_argument("--codex-timeout", type=float, default=900.0)
    c.add_argument(
        "--codex-dry-run",
        action="store_true",
        help="Plan Codex launch without executing (command construction only)",
    )
    c.add_argument(
        "--external-cli-worker",
        action="store_true",
        help="Use ExternalCliWorkerAdapter (provider-neutral; default provider=stub)",
    )
    c.add_argument(
        "--external-cli-provider",
        default="stub",
        help="Observational provider_id: stub|cursor|cursor_agent (not a domain contract)",
    )
    c.add_argument("--external-cli-timeout", type=float, default=900.0)
    c.add_argument(
        "--external-cli-dry-run",
        action="store_true",
        help="Build invocation/command without spawning the CLI",
    )
    c.add_argument("--head-sha", default="c" * 40)
    c.add_argument("--no-context", action="store_true")
    c.set_defaults(func=cmd_step)

    c = sub.add_parser("resume", help="Reload Run from SQLite; optional --step")
    c.add_argument("run_id")
    c.add_argument("--step", action="store_true")
    c.add_argument("--head-sha", default="c" * 40)
    c.set_defaults(func=cmd_resume)

    c = sub.add_parser("bind-worktree", help="Bind an existing isolated worktree to a Run")
    c.add_argument("run_id")
    c.add_argument("--worktree", required=True)
    c.add_argument("--branch", default=None)
    c.add_argument("--base-sha", default=None)
    c.set_defaults(func=cmd_bind_worktree)

    c = sub.add_parser("observe", help="Read-only GitHub/CI observation (manual)")
    c.add_argument("run_id")
    c.add_argument("--pr", required=True, type=int, help="Pull request number")
    c.add_argument("--repo", default=None, help="owner/name (default from Run project)")
    c.add_argument(
        "--fixture-json",
        default=None,
        help="Fake adapter payload path (unit/CI; skips live gh)",
    )
    c.set_defaults(func=cmd_observe)

    c = sub.add_parser("approve", help="Founder Approval (control-plane trusted path)")
    c.add_argument("run_id")
    c.add_argument("--action", required=True, help="e.g. merge, approve_effect")
    c.add_argument("--head-sha", required=True)
    c.add_argument("--actor", default="founder")
    c.add_argument("--scope", default=None)
    c.add_argument("--external-ref", default=None)
    c.add_argument("--expires-at", default=None)
    c.set_defaults(func=cmd_approve)


    c = sub.add_parser("effect", help="Execute allowlisted GitHub PR effect")
    c.add_argument("run_id")
    c.add_argument("--action", required=True, choices=["github_pr_create", "github_pr_comment", "github_pr_merge"])
    c.add_argument("--repo", default="jerry200176-png/portfolio-ops")
    c.add_argument("--target", default=None)
    c.add_argument("--pr", type=int, default=None)
    c.add_argument("--title", default=None)
    c.add_argument("--body", default=None)
    c.add_argument("--head", default=None)
    c.add_argument("--observed-head-sha", default=None)
    c.add_argument("--require-ci", action="store_true")
    c.add_argument("--fake", action="store_true", help="Use FakeGitHubMutator (tests)")
    c.set_defaults(func=cmd_effect)

    c = sub.add_parser("reconcile", help="Bounded observe+reconcile for a Run")
    c.add_argument("run_id")
    c.add_argument("--pr", type=int, default=None)
    c.add_argument("--repo", default=None)
    c.add_argument("--fixture-json", default=None)
    c.set_defaults(func=cmd_reconcile)

    c = sub.add_parser("schedule-tick", help="Single scheduler tick (no daemon)")
    c.add_argument("--limit", type=int, default=5)
    c.add_argument("--pr", type=int, default=None)
    c.add_argument("--head-sha", default="c" * 40)
    c.add_argument("--real-codex", action="store_true")
    c.add_argument("--codex-timeout", type=float, default=900.0)
    c.add_argument("--fake", action="store_true", help="Use FakeGitHubMutator (tests)")
    c.set_defaults(func=cmd_schedule_tick)

    c = sub.add_parser("schedule-run", help="Autonomous single-host scheduler loop")
    c.add_argument("--project", default="portfolio-ops")
    c.add_argument("--limit", type=int, default=5, help="Runs examined per tick")
    c.add_argument("--poll-interval", type=float, default=2.0)
    c.add_argument("--max-poll-interval", type=float, default=30.0)
    c.add_argument("--lease-ttl", type=float, default=30.0)
    c.add_argument("--max-ticks", type=int, default=None)
    c.add_argument("--real-codex", action="store_true")
    c.add_argument("--codex-timeout", type=float, default=900.0)
    c.add_argument("--fake", action="store_true", help="Use FakeGitHubMutator (tests)")
    c.add_argument("--no-signals", action="store_true")
    c.set_defaults(func=cmd_schedule_run)

    c = sub.add_parser("schedule-status", help="Scheduler ownership and runnable Runs")
    c.add_argument("--project", default="portfolio-ops")
    c.set_defaults(func=cmd_schedule_status)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
