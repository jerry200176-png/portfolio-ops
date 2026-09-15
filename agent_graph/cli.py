"""Minimal CLI for durable Graph Control Plane Phase 1A.

Commands:
  run-create | status | step | events | resume | bind-worktree
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .durable_runtime import DurableGraphRuntime
from .harness import FakeWorkerAdapter, GraphHarness
from .sqlite_store import SqliteControlPlaneStore
from .worktree_bind import bind_existing_worktree

DEFAULT_DB = Path(__file__).resolve().parents[1] / "state" / "graph-control.sqlite"


def _runtime(db: str) -> DurableGraphRuntime:
    return DurableGraphRuntime(SqliteControlPlaneStore(db))


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
        worker = FakeWorkerAdapter(head_sha=args.head_sha) if args.fake_worker else FakeWorkerAdapter()
        # Phase 1A default worker is fake; file worker is opt-in later.
        result = harness.step(args.run_id, worker=worker, write_context=not args.no_context)
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
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


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="graph", description="Durable Graph Control Plane CLI (Phase 1A)")
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

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
