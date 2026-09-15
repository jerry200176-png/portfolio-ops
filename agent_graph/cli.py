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

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
