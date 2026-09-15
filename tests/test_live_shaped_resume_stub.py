"""Prove a live-shaped Run (failed usage-limit attempt, waiting_worker) resumes.

Mirrors tip re-exec after Codex quota: new AutonomousSchedulerLoop loads an
existing Run that already has a failed investigator attempt, then RealCodex
(stub) must retry and reach closed_success. Does not touch the live dogfood DB.
"""

from __future__ import annotations

import json
import os
import stat
import subprocess
import tempfile
import textwrap
import time
import unittest
from pathlib import Path
from unittest import mock

from agent_graph.dogfood_evidence import collect_dogfood_evidence
from agent_graph.durable_runtime import DurableGraphRuntime
from agent_graph.github_mutate import FakeGitHubMutator
from agent_graph.github_observe import FakeGitHubReader
from agent_graph.real_codex_adapter import RealCodexWorkerAdapter
from agent_graph.reconciler import GraphReconciler
from agent_graph.scheduler import AutonomousSchedulerLoop
from agent_graph.sqlite_store import SqliteControlPlaneStore

ROUTE_DRY_PLAN = (
    '{"profile":"terra","model":"stub","reasoning_effort_override":null,'
    '"reason":"t","resolution":"selected","requested_tier":"terra","selected_tier":"terra"}'
)


class LiveShapedResumeStubTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.db = self.root / "control" / "g.sqlite"
        self.db.parent.mkdir(parents=True)
        self.worktree = self.root / "wt"
        self.worktree.mkdir()
        subprocess.run(
            ["git", "init", "-b", "main"], cwd=self.worktree, check=True, capture_output=True
        )
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=self.worktree,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "test"],
            cwd=self.worktree,
            check=True,
            capture_output=True,
        )
        (self.worktree / "README.md").write_text("init\n", encoding="utf-8")
        subprocess.run(
            ["git", "add", "README.md"], cwd=self.worktree, check=True, capture_output=True
        )
        subprocess.run(
            ["git", "commit", "-m", "init"], cwd=self.worktree, check=True, capture_output=True
        )
        self.base = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=self.worktree, text=True
        ).strip()
        self.branch = "chore/live-shaped-resume"
        subprocess.run(
            ["git", "checkout", "-b", self.branch],
            cwd=self.worktree,
            check=True,
            capture_output=True,
        )

        self.marker = "docs/agent-graph/real-codex-e2e-marker-live-shaped.md"
        self.route = self.root / "codex-route-stub"
        self.route.write_text(
            textwrap.dedent(
                f"""\
                #!/usr/bin/env bash
                set -euo pipefail
                for a in "$@"; do
                  if [[ "$a" == "--dry-run" ]]; then
                    echo '{ROUTE_DRY_PLAN}'
                    exit 0
                  fi
                done
                wt="${{WORKTREE:-.}}"
                node="${{NODE:-investigator}}"
                attempt="${{ATTEMPT_ID:-att}}"
                mkdir -p "$wt/.agent-session" "$wt/docs/agent-graph"
                if [[ "$node" == "investigator" ]]; then
                  cat > "$wt/.agent-session/result.json" <<EOF
                {{
                  "schema_version": "1.0",
                  "status": "success",
                  "summary": "resume investigation ok",
                  "idempotency_key": "$attempt:INVESTIGATION_COMPLETED",
                  "artifacts": [],
                  "evidence": [{{"kind":"stub","ref":"$attempt","summary":"ok"}}],
                  "proposed_outcome": {{
                    "outcome_type": "INVESTIGATION_COMPLETED",
                    "actor_id": "codex-$attempt",
                    "actor_role": "investigator",
                    "head_sha": null,
                    "base_sha": null,
                    "conclusion": "ok",
                    "evidence": {{"source":"stub"}},
                    "repository": "jerry200176-png/portfolio-ops"
                  }}
                }}
                EOF
                  exit 0
                fi
                if [[ "$node" == "builder" ]]; then
                  printf '%s\\n' '# live-shaped marker' > "$wt/{self.marker}"
                  git -C "$wt" add {self.marker}
                  git -C "$wt" commit -m "docs: live-shaped marker" >/dev/null
                  head=$(git -C "$wt" rev-parse HEAD)
                  cat > "$wt/.agent-session/result.json" <<EOF
                {{
                  "schema_version": "1.0",
                  "status": "success",
                  "summary": "resume build ok",
                  "idempotency_key": "$attempt:BUILD_COMPLETED",
                  "artifacts": [{{"kind":"file","uri":"{self.marker}"}}],
                  "evidence": [{{"kind":"stub","ref":"$attempt","summary":"built"}}],
                  "proposed_outcome": {{
                    "outcome_type": "BUILD_COMPLETED",
                    "actor_id": "codex-$attempt",
                    "actor_role": "builder",
                    "head_sha": "$head",
                    "base_sha": null,
                    "conclusion": "ok",
                    "evidence": {{"source":"stub"}},
                    "repository": "jerry200176-png/portfolio-ops"
                  }}
                }}
                EOF
                  exit 0
                fi
                echo "unexpected node=$node" >&2
                exit 2
                """
            ),
            encoding="utf-8",
        )
        self.route.chmod(self.route.stat().st_mode | stat.S_IEXEC)

        self.store = SqliteControlPlaneStore(str(self.db))
        self.rt = DurableGraphRuntime(self.store)
        objective = (
            "R1 portfolio-ops maintenance (RealCodex end-to-end dogfood).\n\n"
            f"Marker path: {self.marker}\n"
        )
        self.run = self.rt.create_run(
            objective=objective,
            project="portfolio-ops",
            risk_tier="R1",
            success_condition="Marker merged via Effect Journal; Run closed_success",
            base_sha=self.base,
            worktree=str(self.worktree),
            branch=self.branch,
            repository="jerry200176-png/portfolio-ops",
        )
        # Seed a failed usage-limit investigator attempt like the live dogfood DB.
        attempt = self.rt.start_attempt(
            self.run.run_id, worker_type="codex", model_profile="codex-route", worker_pid=1
        )
        attempt.status = "failed"
        attempt.result_ingest_key = f"{attempt.attempt_id}:USAGE_LIMIT"
        from datetime import datetime, timezone

        attempt.ended_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        self.store.update_attempt(attempt)
        # Keep projection at waiting_worker / investigator (live shape).
        run = self.rt.get_run(self.run.run_id)
        self.assertEqual(run.status, "waiting_worker")
        self.assertEqual(run.current_node, "investigator")

    def tearDown(self) -> None:
        self.rt.close()
        self.tmp.cleanup()

    def test_existing_failed_usage_limit_attempt_then_closed_success(self) -> None:
        mut = FakeGitHubMutator()
        reader_state: dict = {
            "number": 108,
            "url": "https://example.invalid/pr/108",
            "state": "OPEN",
            "mergedAt": None,
            "mergeable": "MERGEABLE",
            "headRefOid": self.base,
            "statusCheckRollup": [],
        }
        reader = FakeGitHubReader(reader_state)
        reconciler = GraphReconciler(self.rt, reader)

        def _worker_for_run(run_obj):
            if run_obj.current_node in ("investigator", "builder"):
                return RealCodexWorkerAdapter(
                    codex_route=str(self.route),
                    timeout_sec=30,
                    ephemeral=True,
                    canonical_db_path=str(self.db),
                )
            from agent_graph.harness import FakeWorkerAdapter

            return FakeWorkerAdapter(head_sha=run_obj.head_sha or self.base)

        # Fresh loop = tip re-exec process (no in-memory dormancy).
        loop = AutonomousSchedulerLoop(
            self.rt,
            reconciler=reconciler,
            mutator=mut,
            poll_interval_sec=0.01,
            max_poll_interval_sec=0.05,
            sleep_fn=lambda _s: None,
            use_real_codex=True,
            canonical_db_path=str(self.db),
            tick_limit=5,
        )
        loop.scheduler._worker_for_run = _worker_for_run  # type: ignore[method-assign]
        loop.focus_run_ids = {self.run.run_id}
        self.assertTrue(loop.acquire_ownership())
        try:
            with mock.patch(
                "agent_graph.branch_push.try_ensure_branch_pushed",
                return_value={
                    "pushed": False,
                    "already_up_to_date": True,
                    "branch": self.branch,
                },
            ):
                closed = False
                for _ in range(50):
                    loop.tick_once()
                    run_now = self.rt.get_run(self.run.run_id)
                    if run_now.head_sha and run_now.head_sha != self.base:
                        reader_state["headRefOid"] = run_now.head_sha
                        reader_state["statusCheckRollup"] = [
                            {
                                "name": "validate",
                                "status": "COMPLETED",
                                "conclusion": "SUCCESS",
                            }
                        ]
                    if any(
                        e.action == "github_pr_merge" and e.status == "succeeded"
                        for e in self.store.list_effects(self.run.run_id)
                    ):
                        reader_state["state"] = "MERGED"
                        reader_state["mergedAt"] = "2026-09-15T12:00:00Z"
                    if run_now.closed and run_now.status == "closed_success":
                        closed = True
                        break
                self.assertTrue(
                    closed,
                    f"node={self.rt.get_run(self.run.run_id).current_node} "
                    f"status={self.rt.get_run(self.run.run_id).status}",
                )
        finally:
            loop.release_ownership()

        final = self.rt.get_run(self.run.run_id)
        self.assertEqual(final.status, "closed_success")
        attempts = self.store._conn.execute(
            "SELECT status FROM attempts WHERE run_id=? AND node='investigator' ORDER BY started_at",
            (self.run.run_id,),
        ).fetchall()
        # Prior failed USAGE_LIMIT + successful retry (status may be success/ingested/completed).
        self.assertGreaterEqual(len(attempts), 2)
        self.assertEqual(attempts[0][0], "failed")
        self.assertTrue(
            any(a[0] in ("succeeded", "success", "completed", "ingested", "finished") for a in attempts[1:]),
            attempts,
        )
        evidence = collect_dogfood_evidence(
            runtime=self.rt,
            store=self.store,
            run_id=self.run.run_id,
            mode="schedule-run",
        )
        self.assertTrue(evidence["terminal_reconciliation"]["closed_success"])
        self.assertTrue(evidence["implementation_workers_are_codex"])
        inv = [
            w
            for w in evidence["worker_identities"]
            if w["node"] == "investigator" and w["worker_type"] == "codex"
        ]
        self.assertGreaterEqual(len(inv), 2)


if __name__ == "__main__":
    unittest.main()
