"""Unit tests for RealCodexWorkerAdapter (no live Codex required)."""

from __future__ import annotations

import json
import os
import stat
import tempfile
import textwrap
import unittest
from pathlib import Path

from agent_graph.durable_runtime import DurableGraphRuntime
from agent_graph.harness import GraphHarness
from agent_graph.prompt_compiler import compile_node_prompt
from agent_graph.real_codex_adapter import RealCodexWorkerAdapter
from agent_graph.sqlite_store import SqliteControlPlaneStore
from agent_graph.worker_contract import RESULT_REL_PATH, read_worker_result, write_worker_result


def _write_executable(path: Path, body: str) -> Path:
    path.write_text(body, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IEXEC)
    return path


ROUTE_DRY_PLAN = (
    '{"profile":"terra","model":"stub","reasoning_effort_override":null,'
    '"reason":"t","resolution":"selected","requested_tier":"terra","selected_tier":"terra"}'
)


class RealCodexAdapterUnitTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.control = self.root / "control-plane"
        self.control.mkdir()
        self.db = self.control / "graph.sqlite"
        self.worktree = self.root / "wt"
        self.worktree.mkdir()
        (self.worktree / ".git").mkdir()
        self.store = SqliteControlPlaneStore(str(self.db))
        self.rt = DurableGraphRuntime(self.store)
        self.harness = GraphHarness(self.rt)
        self.base_sha = "a" * 40
        self.bin_dir = self.root / "bin"
        self.bin_dir.mkdir()

    def tearDown(self) -> None:
        self.rt.close()
        self.tmp.cleanup()

    def _run(self):
        return self.rt.create_run(
            objective="prove real codex replaceable worker",
            project="portfolio-ops",
            base_sha=self.base_sha,
            worktree=str(self.worktree),
            branch="test-branch",
            success_condition="investigator writes valid result.json",
        )

    def _success_route(self, *, outcome: str, role: str, head: str | None = None) -> Path:
        head = head or self.base_sha
        script = self.bin_dir / f"codex-route-{outcome}-{role}"
        body = textwrap.dedent(
            f"""\
            #!/usr/bin/env bash
            set -euo pipefail
            for a in "$@"; do
              if [[ "$a" == "--dry-run" ]]; then
                echo '{ROUTE_DRY_PLAN}'
                exit 0
              fi
            done
            wt=""
            prev=""
            for arg in "$@"; do
              if [[ "$prev" == "-C" ]]; then wt="$arg"; fi
              prev="$arg"
            done
            mkdir -p "$wt/.agent-session"
            attempt="${{ATTEMPT_ID:?}}"
            cat > "$wt/{RESULT_REL_PATH}" <<EOF
            {{
              "schema_version": "1.0",
              "status": "success",
              "summary": "stub {outcome}",
              "idempotency_key": "${{attempt}}:{outcome}",
              "artifacts": [],
              "evidence": [{{"kind": "fixture", "ref": "${{attempt}}", "summary": "stub"}}],
              "proposed_outcome": {{
                "outcome_type": "{outcome}",
                "actor_id": "stub-{role}-${{attempt}}",
                "actor_role": "{role}",
                "head_sha": "{head}",
                "base_sha": "{self.base_sha}",
                "conclusion": "ok",
                "evidence": {{"source": "stub"}},
                "repository": "jerry200176-png/portfolio-ops"
              }}
            }}
            EOF
            """
        )
        return _write_executable(script, body)

    def _route_stub(self, *, mode: str) -> Path:
        script = self.bin_dir / f"codex-route-{mode}"
        if mode == "success":
            return self._success_route(outcome="INVESTIGATION_COMPLETED", role="investigator")
        if mode == "missing":
            body = textwrap.dedent(
                f"""\
                #!/usr/bin/env bash
                set -euo pipefail
                for a in "$@"; do
                  if [[ "$a" == "--dry-run" ]]; then echo '{ROUTE_DRY_PLAN}'; exit 0; fi
                done
                exit 0
                """
            )
        elif mode == "nonzero":
            body = textwrap.dedent(
                f"""\
                #!/usr/bin/env bash
                set -euo pipefail
                for a in "$@"; do
                  if [[ "$a" == "--dry-run" ]]; then echo '{ROUTE_DRY_PLAN}'; exit 0; fi
                done
                echo boom >&2
                exit 7
                """
            )
        elif mode == "timeout":
            body = textwrap.dedent(
                f"""\
                #!/usr/bin/env bash
                set -euo pipefail
                for a in "$@"; do
                  if [[ "$a" == "--dry-run" ]]; then echo '{ROUTE_DRY_PLAN}'; exit 0; fi
                done
                sleep 30
                """
            )
        elif mode == "malformed":
            body = textwrap.dedent(
                f"""\
                #!/usr/bin/env bash
                set -euo pipefail
                for a in "$@"; do
                  if [[ "$a" == "--dry-run" ]]; then echo '{ROUTE_DRY_PLAN}'; exit 0; fi
                done
                wt=""; prev=""
                for arg in "$@"; do
                  if [[ "$prev" == "-C" ]]; then wt="$arg"; fi
                  prev="$arg"
                done
                mkdir -p "$wt/.agent-session"
                echo '{{"next_node":"builder","status":"success"}}' > "$wt/{RESULT_REL_PATH}"
                """
            )
        else:
            raise AssertionError(mode)
        return _write_executable(script, body)

    def test_command_construction_binds_worktree_and_ephemeral(self) -> None:
        adapter = RealCodexWorkerAdapter(codex_route="/usr/bin/true", dry_run=True)
        cmd = adapter.build_route_command(
            worktree=self.worktree, prompt_text="PROMPT_BODY", dry_run=False
        )
        self.assertEqual(cmd[0], "/usr/bin/true")
        self.assertIn("--", cmd)
        self.assertIn("-C", cmd)
        self.assertEqual(cmd[cmd.index("-C") + 1], str(self.worktree))
        self.assertIn("--ephemeral", cmd)
        self.assertNotIn("resume", cmd)
        self.assertNotIn("--last", cmd)
        self.assertIn("PROMPT_BODY", cmd)

    def test_prompt_compiler_includes_context_contract(self) -> None:
        run = self._run()
        attempt = self.rt.start_attempt(run.run_id, worker_type="codex")
        compiled = compile_node_prompt(
            run=run,
            attempt=attempt,
            goal_objective="prove replaceability",
            worktree=str(self.worktree),
        )
        text = compiled.text
        self.assertIn(run.run_id, text)
        self.assertIn(attempt.attempt_id, text)
        self.assertIn("investigator", text)
        self.assertIn(str(attempt.expected_state_version), text)
        self.assertIn(str(self.worktree), text)
        self.assertIn(RESULT_REL_PATH, text)
        self.assertIn("next_node", text)
        self.assertIn("expected_state_version", text)

    def test_worker_context_propagation(self) -> None:
        run = self._run()
        route = self._route_stub(mode="success")
        adapter = RealCodexWorkerAdapter(codex_route=str(route), timeout_sec=10, canonical_db_path=self.db)
        out = self.harness.step(run.run_id, worker=adapter, write_context=True)
        self.assertTrue(out.apply.accepted)
        ctx = json.loads((self.worktree / ".agent-session/worker-context.json").read_text())
        self.assertEqual(ctx["RUN_ID"], run.run_id)
        self.assertEqual(ctx["ATTEMPT_ID"], out.attempt.attempt_id)
        self.assertEqual(ctx["NODE"], "investigator")
        self.assertEqual(ctx["EXPECTED_STATE_VERSION"], 1)
        self.assertEqual(ctx["WORKTREE"], str(self.worktree))
        self.assertIsNotNone(adapter.last_launch)
        self.assertIsNotNone(adapter.last_launch.pid)
        self.assertEqual(adapter.last_launch.exit_code, 0)

    def test_missing_result_is_deterministic_failure(self) -> None:
        run = self._run()
        route = self._route_stub(mode="missing")
        adapter = RealCodexWorkerAdapter(codex_route=str(route), timeout_sec=10, canonical_db_path=self.db)
        out = self.harness.step(run.run_id, worker=adapter)
        self.assertFalse(out.apply.accepted)
        self.assertEqual(out.attempt.status, "failed")
        self.assertEqual(self.rt.get_run(run.run_id).current_node, "investigator")
        self.assertIn("MISSING_RESULT", out.attempt.result_ingest_key or "")

    def test_nonzero_exit_without_result_fails(self) -> None:
        run = self._run()
        route = self._route_stub(mode="nonzero")
        adapter = RealCodexWorkerAdapter(codex_route=str(route), timeout_sec=10, canonical_db_path=self.db)
        out = self.harness.step(run.run_id, worker=adapter)
        self.assertFalse(out.apply.accepted)
        self.assertEqual(out.attempt.status, "failed")
        self.assertEqual(self.rt.get_run(run.run_id).current_node, "investigator")

    def test_timeout_fails_closed(self) -> None:
        run = self._run()
        route = self._route_stub(mode="timeout")
        adapter = RealCodexWorkerAdapter(codex_route=str(route), timeout_sec=0.5, canonical_db_path=self.db)
        out = self.harness.step(run.run_id, worker=adapter)
        self.assertFalse(out.apply.accepted)
        self.assertTrue(adapter.last_launch.timed_out)
        self.assertEqual(self.rt.get_run(run.run_id).current_node, "investigator")

    def test_malformed_result_fails_closed(self) -> None:
        run = self._run()
        route = self._route_stub(mode="malformed")
        adapter = RealCodexWorkerAdapter(codex_route=str(route), timeout_sec=10, canonical_db_path=self.db)
        out = self.harness.step(run.run_id, worker=adapter)
        self.assertFalse(out.apply.accepted)
        self.assertEqual(out.attempt.status, "failed")
        self.assertEqual(self.rt.get_run(run.run_id).current_node, "investigator")

    def test_death_before_result_preserves_canonical_state(self) -> None:
        run = self._run()
        before = self.rt.get_run(run.run_id).to_dict()
        route = self._route_stub(mode="nonzero")
        adapter = RealCodexWorkerAdapter(codex_route=str(route), timeout_sec=10, canonical_db_path=self.db)
        out = self.harness.step(run.run_id, worker=adapter)
        self.assertFalse(out.apply.accepted)
        after = self.rt.get_run(run.run_id)
        self.assertEqual(after.current_node, before["current_node"])
        self.assertEqual(after.state_version, before["state_version"])
        types = [e.type for e in self.rt.list_events(run.run_id)]
        self.assertEqual(types, ["TASK_CREATED"])

    def test_stale_result_fail_closed_after_successful_sibling(self) -> None:
        run = self._run()
        a = self.rt.start_attempt(run.run_id, worker_type="codex")
        b = self.rt.start_attempt(run.run_id, worker_type="codex")
        self.assertEqual(a.expected_state_version, b.expected_state_version)
        self.assertEqual(a.node, "investigator")

        def result_for(attempt_id: str) -> dict:
            return {
                "schema_version": "1.0",
                "status": "success",
                "summary": "ok",
                "idempotency_key": f"{attempt_id}:INVESTIGATION_COMPLETED",
                "artifacts": [],
                "evidence": [{"kind": "t", "ref": attempt_id}],
                "proposed_outcome": {
                    "outcome_type": "INVESTIGATION_COMPLETED",
                    "actor_id": f"inv-{attempt_id[-6:]}",
                    "actor_role": "investigator",
                    "head_sha": self.base_sha,
                    "base_sha": self.base_sha,
                    "conclusion": "ok",
                    "evidence": {},
                    "repository": "jerry200176-png/portfolio-ops",
                },
            }

        first = self.harness.ingest_worker_result(
            run_id=run.run_id, attempt_id=a.attempt_id, result=result_for(a.attempt_id)
        )
        self.assertTrue(first.apply.accepted)
        second = self.harness.ingest_worker_result(
            run_id=run.run_id, attempt_id=b.attempt_id, result=result_for(b.attempt_id)
        )
        self.assertFalse(second.apply.accepted)
        self.assertEqual(second.apply.blocker, "stale_state_version")

    def test_stub_a_to_b_replacement_without_shared_thread(self) -> None:
        run = self._run()
        route = self._route_stub(mode="success")
        a = RealCodexWorkerAdapter(codex_route=str(route), timeout_sec=10, canonical_db_path=self.db)
        out_a = self.harness.step(run.run_id, worker=a)
        self.assertTrue(out_a.apply.accepted)
        pid_a = a.last_launch.pid
        self.assertIsNotNone(pid_a)
        try:
            os.kill(pid_a, 0)
            alive = True
        except ProcessLookupError:
            alive = False
        self.assertFalse(alive)

        self.rt.close()
        store2 = SqliteControlPlaneStore(str(self.db))
        rt2 = DurableGraphRuntime(store2)
        harness2 = GraphHarness(rt2)
        self.assertEqual(rt2.get_run(run.run_id).current_node, "builder")

        builder = self._success_route(
            outcome="BUILD_COMPLETED", role="builder", head="b" * 40
        )
        b = RealCodexWorkerAdapter(codex_route=str(builder), timeout_sec=10, canonical_db_path=self.db)
        out_b = harness2.step(run.run_id, worker=b)
        self.assertTrue(out_b.apply.accepted, msg=out_b.apply.reason)
        self.assertNotEqual(a.last_launch.pid, b.last_launch.pid)
        self.assertNotIn("resume", b.last_launch.command)
        self.assertEqual(rt2.get_run(run.run_id).current_node, "reviewer")
        rt2.close()

    def test_refuse_home_worktree(self) -> None:
        run = self.rt.create_run(
            objective="bad",
            project="portfolio-ops",
            base_sha=self.base_sha,
            worktree="/home/jerry",
        )
        adapter = RealCodexWorkerAdapter(codex_route=str(self._route_stub(mode="missing")), canonical_db_path=self.db)
        with self.assertRaises(Exception):
            adapter.execute(
                run=run,
                attempt=self.rt.start_attempt(run.run_id, worker_type="codex"),
                context={"WORKTREE": "/home/jerry", "GOAL_OBJECTIVE": "x"},
            )


if __name__ == "__main__":
    unittest.main()
