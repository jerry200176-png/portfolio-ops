"""Schedule + RealCodexWorkerAdapter stub path reaches closed_success.

Uses a stub ``codex-route`` (not FakeWorker) so investigator/builder still go
through RealCodexWorkerAdapter with ephemeral launch, leases, and result ingest.
"""

from __future__ import annotations

import json
import os
import stat
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest import mock

from agent_graph.durable_runtime import DurableGraphRuntime
from agent_graph.github_mutate import FakeGitHubMutator
from agent_graph.github_observe import FakeGitHubReader
from agent_graph.real_codex_adapter import RealCodexWorkerAdapter
from agent_graph.reconciler import GraphReconciler
from agent_graph.scheduler import AutonomousSchedulerLoop, GraphScheduler
from agent_graph.sqlite_store import SqliteControlPlaneStore


ROUTE_DRY_PLAN = (
    '{"profile":"terra","model":"stub","reasoning_effort_override":null,'
    '"reason":"t","resolution":"selected","requested_tier":"terra","selected_tier":"terra"}'
)


class ScheduleRealCodexStubE2ETests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.db = self.root / "control" / "g.sqlite"
        self.db.parent.mkdir(parents=True)
        self.worktree = self.root / "wt"
        self.worktree.mkdir()
        subprocess.run(["git", "init", "-b", "main"], cwd=self.worktree, check=True, capture_output=True)
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
        subprocess.run(["git", "add", "README.md"], cwd=self.worktree, check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "init"], cwd=self.worktree, check=True, capture_output=True
        )
        self.base = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=self.worktree, text=True
        ).strip()
        self.branch = "chore/stub-dogfood"
        subprocess.run(
            ["git", "checkout", "-b", self.branch],
            cwd=self.worktree,
            check=True,
            capture_output=True,
        )

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
                  "summary": "stub investigation ok",
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
                  printf '%s\\n' '# stub marker' > "$wt/docs/agent-graph/real-codex-e2e-marker.md"
                  git -C "$wt" add docs/agent-graph/real-codex-e2e-marker.md
                  git -C "$wt" commit -m "docs: stub marker" >/dev/null
                  head=$(git -C "$wt" rev-parse HEAD)
                  cat > "$wt/.agent-session/result.json" <<EOF
                {{
                  "schema_version": "1.0",
                  "status": "success",
                  "summary": "stub build ok",
                  "idempotency_key": "$attempt:BUILD_COMPLETED",
                  "artifacts": [{{"kind":"file","uri":"docs/agent-graph/real-codex-e2e-marker.md"}}],
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
        self.head_after_build = None

    def tearDown(self) -> None:
        self.rt.close()
        self.tmp.cleanup()

    def test_stub_realcodex_schedule_reaches_closed_success(self) -> None:
        run = self.rt.create_run(
            objective="stub RealCodex schedule dogfood",
            project="portfolio-ops",
            risk_tier="R1",
            base_sha=self.base,
            worktree=str(self.worktree),
            branch=self.branch,
        )
        mut = FakeGitHubMutator()
        reader_state: dict = {
            "number": 42,
            "url": "https://example.invalid/pr/42",
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

        sched = GraphScheduler(
            self.rt,
            reconciler=reconciler,
            mutator=mut,
            use_real_codex=True,
            canonical_db_path=str(self.db),
        )
        sched._worker_for_run = _worker_for_run  # type: ignore[method-assign]

        # Advance until closed_success (policy gate + effects + reconcile).
        actions = []
        with mock.patch(
            "agent_graph.branch_push.try_ensure_branch_pushed",
            return_value={"pushed": False, "already_up_to_date": True, "branch": self.branch},
        ):
            for _ in range(20):
                tick = sched.tick(limit=5)
                actions.extend(tick.advanced)
                run_now = self.rt.get_run(run.run_id)
                if run_now.head_sha and run_now.head_sha != self.base:
                    reader_state["headRefOid"] = run_now.head_sha
                    reader_state["statusCheckRollup"] = [
                        {"name": "validate", "status": "COMPLETED", "conclusion": "SUCCESS"}
                    ]
                if run_now.closed and run_now.status == "closed_success":
                    break
                if any(
                    e.action == "github_pr_merge" and e.status == "succeeded"
                    for e in self.store.list_effects(run.run_id)
                ):
                    reader_state["state"] = "MERGED"
                    reader_state["mergedAt"] = "2026-09-15T12:00:00Z"
            else:
                self.fail(
                    f"did not close: node={self.rt.get_run(run.run_id).current_node} "
                    f"status={self.rt.get_run(run.run_id).status} "
                    f"actions={[a.get('action') for a in actions]}"
                )

        final = self.rt.get_run(run.run_id)
        self.assertEqual(final.status, "closed_success")
        self.assertEqual(final.current_node, "close")
        attempts = [
            dict(r)
            for r in self.store._conn.execute(
                "SELECT node, worker_type, status FROM attempts WHERE run_id=? ORDER BY started_at",
                (run.run_id,),
            )
        ]
        inv = [a for a in attempts if a["node"] == "investigator"]
        bld = [a for a in attempts if a["node"] == "builder"]
        self.assertTrue(inv and inv[0]["worker_type"] == "codex")
        self.assertTrue(bld and bld[0]["worker_type"] == "codex")
        self.assertTrue((self.worktree / "docs/agent-graph/real-codex-e2e-marker.md").is_file())
        self.assertTrue(any(e.action == "github_pr_merge" for e in self.store.list_effects(run.run_id)))

    def test_quota_limit_then_resume_reaches_closed_success(self) -> None:
        """First RealCodex hit dormants on usage-limit; after resume epoch → closed_success.

        Mirrors the live wait-through dogfood: AutonomousSchedulerLoop + RealCodex
        investigator/builder, then control-plane reviewer/effects. Proves the only
        live blocker is ChatGPT quota, not control-plane resume wiring.
        """
        import time

        from agent_graph.dogfood_evidence import collect_dogfood_evidence

        counter = self.root / "quota_hits"
        counter.write_text("0", encoding="utf-8")
        # First non-dry-run invocation fails with usage-limit; later succeed like stub.
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
                cfile="{counter}"
                n=$(cat "$cfile")
                echo $((n+1)) > "$cfile"
                if [[ "$n" -eq 0 ]]; then
                  echo "ERROR: You've hit your usage limit. Visit https://chatgpt.com/codex/settings/usage to purchase more credits or try again at Sep 19th, 2026 4:26 PM." >&2
                  exit 1
                fi
                wt="${{WORKTREE:-.}}"
                node="${{NODE:-investigator}}"
                attempt="${{ATTEMPT_ID:-att}}"
                mkdir -p "$wt/.agent-session" "$wt/docs/agent-graph"
                if [[ "$node" == "investigator" ]]; then
                  cat > "$wt/.agent-session/result.json" <<EOF
                {{
                  "schema_version": "1.0",
                  "status": "success",
                  "summary": "post-quota investigation ok",
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
                  printf '%s\\n' '# post-quota marker' > "$wt/docs/agent-graph/real-codex-e2e-marker.md"
                  git -C "$wt" add docs/agent-graph/real-codex-e2e-marker.md
                  git -C "$wt" commit -m "docs: post-quota marker" >/dev/null
                  head=$(git -C "$wt" rev-parse HEAD)
                  cat > "$wt/.agent-session/result.json" <<EOF
                {{
                  "schema_version": "1.0",
                  "status": "success",
                  "summary": "post-quota build ok",
                  "idempotency_key": "$attempt:BUILD_COMPLETED",
                  "artifacts": [{{"kind":"file","uri":"docs/agent-graph/real-codex-e2e-marker.md"}}],
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

        run = self.rt.create_run(
            objective="quota-resume RealCodex schedule dogfood",
            project="portfolio-ops",
            risk_tier="R1",
            base_sha=self.base,
            worktree=str(self.worktree),
            branch=self.branch,
        )
        mut = FakeGitHubMutator()
        reader_state: dict = {
            "number": 77,
            "url": "https://example.invalid/pr/77",
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
        loop.focus_run_ids = {run.run_id}
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
                t1 = loop.tick_once()
                self.assertTrue(
                    any(a.get("action") == "dormant_codex_usage_limit" for a in t1.advanced),
                    t1.to_dict(),
                )
                self.assertIn(run.run_id, loop._codex_dormant_until)
                self.assertNotIn(run.run_id, loop._permanent_blockers)
                # Still dormant → skipped
                t2 = loop.tick_once()
                self.assertTrue(t2.idle)
                # Resume epoch passes (live dogfood sleeps here).
                loop._codex_dormant_until[run.run_id] = time.time() - 1
                closed = False
                for _ in range(40):
                    tick = loop.tick_once()
                    run_now = self.rt.get_run(run.run_id)
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
                        for e in self.store.list_effects(run.run_id)
                    ):
                        reader_state["state"] = "MERGED"
                        reader_state["mergedAt"] = "2026-09-15T12:00:00Z"
                    if run_now.closed and run_now.status == "closed_success":
                        closed = True
                        break
                self.assertTrue(
                    closed,
                    f"node={self.rt.get_run(run.run_id).current_node} "
                    f"status={self.rt.get_run(run.run_id).status}",
                )
        finally:
            loop.release_ownership()

        final = self.rt.get_run(run.run_id)
        self.assertEqual(final.status, "closed_success")
        evidence = collect_dogfood_evidence(
            runtime=self.rt, store=self.store, run_id=run.run_id, mode="schedule-run"
        )
        self.assertTrue(evidence["terminal_reconciliation"]["closed_success"])
        self.assertEqual(evidence["mode"], "schedule-run")
        self.assertTrue(evidence["implementation_workers_are_codex"])
        self.assertTrue(evidence["effect_ids"])
        self.assertTrue(evidence["pr"]["number"])
        self.assertTrue(evidence["exact_head_sha"])
        # Investigator had a failed usage-limit attempt then a success.
        inv = [
            w
            for w in evidence["worker_identities"]
            if w["node"] == "investigator" and w["worker_type"] == "codex"
        ]
        self.assertGreaterEqual(len(inv), 2)


if __name__ == "__main__":
    unittest.main()
