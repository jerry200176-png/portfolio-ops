import importlib.util
import contextlib
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
import datetime as dt
import shutil
import sys
import os
from datetime import datetime
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "agent-control/lib"))
from lifecycle_event import make_event, validate_event
SPEC = importlib.util.spec_from_file_location("artifact_gc", ROOT / "agent-control/lib/artifact_gc.py")
GC = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GC)
ADAPTER_SPEC = importlib.util.spec_from_file_location("exo_completion", ROOT / "agent-control/lib/exo_completion.py")
ADAPTER = importlib.util.module_from_spec(ADAPTER_SPEC)
ADAPTER_SPEC.loader.exec_module(ADAPTER)


class ArtifactGCTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.safe = base / "tasks"
        self.worktree = self.safe / "sample"
        self.worktree.mkdir(parents=True)
        self.sessions = base / "sessions"
        self.sessions.mkdir()
        self._git("init", "-q")
        self._git("config", "user.email", "test@example.invalid")
        self._git("config", "user.name", "Test")
        (self.worktree / ".gitignore").write_text("node_modules/\n.next/\n.agent-session/manifest.json\n")
        (self.worktree / "package.json").write_text(json.dumps({
            "scripts": {"build": "next build"}, "dependencies": {"next": "1.0.0"}
        }))
        (self.worktree / "package-lock.json").write_text("{}")
        (self.worktree / "src.js").write_text("keep source")
        self._git("add", ".gitignore", "package.json", "package-lock.json", "src.js")
        self._git("commit", "-qm", "fixture")
        self.manifest = {"session_id": "session-1", "project": "portfolio-ops",
                         "task_id": "sample", "provenance_type": "agent-session",
                         "worktree_path": str(self.worktree)}
        (self.sessions / "session-1.json").write_text(json.dumps(self.manifest))
        (self.worktree / ".agent-session").mkdir()
        (self.worktree / ".agent-session/manifest.json").write_text(json.dumps(self.manifest))
        self.policy = json.loads((ROOT / "agent-control/config/artifact-gc.json").read_text())

    def tearDown(self):
        self.tmp.cleanup()

    def _git(self, *args):
        return subprocess.run(["git", "-C", str(self.worktree), *args], check=True,
                              capture_output=True, text=True)

    def _artifacts(self):
        modules = self.worktree / "node_modules"
        modules.mkdir(exist_ok=True)
        (modules / "generated.bin").write_bytes(b"x" * 4096)
        build = self.worktree / ".next"
        build.mkdir(exist_ok=True)
        (build / "generated.bin").write_bytes(b"y" * 4096)
        return modules, build

    def _evaluate(self, **kwargs):
        return GC.evaluate(self.worktree, self.sessions, self.policy, [self.safe], [], True, **kwargs)

    def _receive_event(self, event, processes=None, *, real_process_scan=False):
        log = Path(self.tmp.name) / "logs/lifecycle-events.jsonl"
        original_run = GC.run

        def run(*args):
            if len(args) >= 5 and args[0] == "git" and args[-2:] == ("list", "--porcelain"):
                return subprocess.CompletedProcess(args, 0, f"worktree {self.worktree}\n", "")
            return original_run(*args)

        argv = ["finish", "--config", str(ROOT / "agent-control/config/artifact-gc.json"),
                "--session-dir", str(self.sessions), "--worktree", str(self.worktree),
                "--bare", str(Path(self.tmp.name) / "unused.git"), "--task-root", str(self.safe),
                "--quarantine-root", str(Path(self.tmp.name) / "quarantine"),
                "--task-id", "sample", "--event-stdin", "--event-log", str(log)]
        output = io.StringIO()
        scan_patch = (contextlib.nullcontext() if real_process_scan else
                      mock.patch.object(GC, "process_snapshot", return_value=(processes or [], True)))
        with mock.patch.object(GC, "run", side_effect=run), scan_patch, \
             mock.patch("sys.stdin", io.StringIO(json.dumps(event))), contextlib.redirect_stdout(output):
            self.assertEqual(GC.main(argv), 0)
        return json.loads(output.getvalue()), log

    def test_terminal_dirty_source_keeps_source_but_reclaims_locked_artifacts(self):
        modules, build = self._artifacts()
        user_file = self.worktree / "notes.txt"
        user_file.write_text("untracked work")
        head_before = self._git("rev-parse", "HEAD").stdout.strip()
        status_before = self._git("status", "--porcelain=v1", "--untracked-files=all").stdout
        git_entries_before = sorted(p.relative_to(self.worktree / ".git").as_posix()
                                    for p in (self.worktree / ".git").rglob("*"))
        result = self._evaluate(terminal_signal=True)
        self.assertEqual(result["state"], "eligible")
        self.assertEqual({a["kind"] for a in result["artifacts"]}, {"node_modules"})
        with mock.patch.object(GC, "process_snapshot", return_value=([], True)):
            collected = self._evaluate(terminal_signal=True, dry_run=False)
        self.assertTrue(collected["state"] == "eligible")
        self.assertFalse(modules.exists())
        self.assertTrue(build.exists())
        self.assertEqual((self.worktree / "src.js").read_text(), "keep source")
        self.assertEqual(user_file.read_text(), "untracked work")
        self.assertTrue(self.worktree.exists())
        self.assertEqual(self._git("rev-parse", "HEAD").stdout.strip(), head_before)
        self.assertEqual(self._git("status", "--porcelain=v1", "--untracked-files=all").stdout,
                         status_before)
        self.assertEqual(sorted(p.relative_to(self.worktree / ".git").as_posix()
                                for p in (self.worktree / ".git").rglob("*")), git_entries_before)

    def test_canary_policy_allows_only_node_modules(self):
        self.assertEqual([target["name"] for target in self.policy["targets"]], ["node_modules"])

    def test_active_process_cwd_blocks_collection(self):
        self._artifacts()
        result = GC.evaluate(self.worktree, self.sessions, self.policy, [self.safe],
                             [{"pid": 42, "cwd": self.worktree}], True, terminal_signal=True)
        self.assertEqual((result["state"], result["reason"]), ("active", "process_uses_worktree"))

    def test_open_file_in_worktree_blocks_collection(self):
        self._artifacts()
        result = GC.evaluate(self.worktree, self.sessions, self.policy, [self.safe],
                             [{"pid": 44, "cwd": Path("/tmp"),
                               "open_paths": [self.worktree / "src.js"]}], True,
                             terminal_signal=True)
        self.assertEqual((result["state"], result["reason"]),
                         ("active", "process_open_worktree"))

    def test_incomplete_process_scan_fails_closed(self):
        self._artifacts()
        result = GC.evaluate(self.worktree, self.sessions, self.policy, [self.safe],
                             [], False, terminal_signal=True)
        self.assertEqual((result["state"], result["reason"]),
                         ("active", "process_scan_incomplete"))

    def test_active_session_identity_blocks_even_outside_worktree(self):
        self._artifacts()
        result = GC.evaluate(self.worktree, self.sessions, self.policy, [self.safe],
                             [{"pid": 43, "cwd": Path("/tmp"), "session_id": "session-1"}],
                             True, terminal_signal=True)
        self.assertEqual(result["state"], "active")

    def test_unexpired_lease_blocks_collection(self):
        self._artifacts()
        lock = self.worktree / ".exo/locks/ticket.lock.json"
        lock.parent.mkdir(parents=True)
        lock.write_text(json.dumps({"expires_at": (dt.datetime.now(dt.timezone.utc)
                         + dt.timedelta(hours=1)).isoformat()}))
        result = self._evaluate(terminal_signal=True)
        self.assertEqual(result["reason"], "active_lease")

    def test_next_output_is_outside_node_modules_canary_scope(self):
        _, build = self._artifacts()
        (build / "tracked.js").write_text("deliverable")
        self._git("add", "-f", ".next/tracked.js")
        result = self._evaluate(terminal_signal=True)
        self.assertFalse(any(a["kind"] == ".next" for a in result["artifacts"]))
        self.assertTrue((build / "tracked.js").exists())

    def test_node_modules_without_a_lockfile_is_not_proven_regenerable(self):
        modules, _ = self._artifacts()
        (self.worktree / "package-lock.json").unlink()
        result = self._evaluate(terminal_signal=True)
        self.assertFalse(any(a["kind"] == "node_modules" for a in result["artifacts"]))
        self.assertTrue(modules.exists())

    def test_quarantine_without_owner_reason_and_terminal_metadata_is_skipped(self):
        qroot = Path(self.tmp.name) / "quarantine" / "alltrue"
        qwork = qroot / "sample"
        qroot.mkdir(parents=True)
        shutil.copytree(self.worktree, qwork)
        (qwork / "node_modules").mkdir()
        (qwork / "node_modules/generated.bin").write_bytes(b"x" * 4096)
        self.manifest["worktree_path"] = str(qwork)
        (self.sessions / "session-1.json").write_text(json.dumps(self.manifest))
        (qwork / ".agent-session/manifest.json").write_text(json.dumps(self.manifest))
        result = GC.evaluate(qwork, self.sessions, self.policy, [qroot], [], True,
                             terminal_signal=True)
        self.assertEqual(result["reason"], "quarantine_metadata_incomplete")
        self.assertTrue((qwork / "node_modules").exists())

    def test_no_terminal_record_means_workspace_sweep_skips(self):
        self._artifacts()
        result = self._evaluate()
        self.assertEqual((result["state"], result["reason"]), ("unknown", "not_confirmed_terminal"))

    def test_repeated_collection_is_idempotent_and_preserves_worktree(self):
        self._artifacts()
        with mock.patch.object(GC, "process_snapshot", return_value=([], True)):
            self._evaluate(terminal_signal=True, dry_run=False)
        manifest = self.sessions / "session-1.json"
        first = json.loads(manifest.read_text())
        self.assertEqual(first["lifecycle_state"], "terminal")
        stamp = first["lifecycle_updated_at"]
        with mock.patch.object(GC, "process_snapshot", return_value=([], True)):
            self._evaluate(terminal_signal=True, dry_run=False)
        second = json.loads(manifest.read_text())
        self.assertEqual(second["lifecycle_updated_at"], stamp)
        self.assertTrue(self.worktree.exists())
        self.assertFalse((self.worktree / "node_modules").exists())

    def test_cli_shutdown_marks_idle_but_does_not_reclaim_before_task_terminal(self):
        self.assertTrue((ROOT / "agent-control/bin/agent-finish").stat().st_mode & 0o111)
        modules, _ = self._artifacts()
        with mock.patch.object(GC, "process_snapshot", return_value=([], True)):
            result = self._evaluate(terminal_signal=True, lifecycle_state="idle", dry_run=False)
        manifest = json.loads((self.sessions / "session-1.json").read_text())
        self.assertEqual(manifest["lifecycle_state"], "idle")
        self.assertTrue(manifest["lifecycle_updated_at"])
        self.assertTrue(modules.exists())
        self.assertTrue(self.worktree.exists())
        self.assertEqual((result["state"], result["reason"]),
                         ("unknown", "task_not_terminal"))

    def test_capacity_limits_are_configured_not_duplicated(self):
        changed = {**self.policy, "capacity_gib": {"pressure_below": 70, "critical_below": 40}}
        self.assertEqual(GC.pressure(changed, 75 * 1024**3), "NORMAL")
        self.assertEqual(GC.pressure(changed, 55 * 1024**3), "PRESSURE")
        self.assertEqual(GC.pressure(changed, 35 * 1024**3), "CRITICAL")

    def test_identical_terminal_event_is_logged_once_and_repeat_cleanup_is_safe(self):
        modules, _ = self._artifacts()
        event = make_event("sample", self.worktree, "terminal_success", "test",
                           "2026-09-24T10:00:00Z")
        log = Path(self.tmp.name) / "events.jsonl"
        self.assertTrue(GC.record_event(log, event))
        self.assertFalse(GC.record_event(log, event))
        self.assertEqual(len(log.read_text().splitlines()), 1)
        with mock.patch.object(GC, "process_snapshot", return_value=([], True)):
            first = self._evaluate(terminal_signal=True, dry_run=False)
            second = self._evaluate(terminal_signal=True, dry_run=False)
        self.assertEqual(first["state"], "eligible")
        self.assertEqual(second["state"], "eligible")
        self.assertFalse(modules.exists())
        self.assertEqual(second["artifacts"], [])

    def test_canonical_idle_failed_and_aborted_events_never_trigger_gc(self):
        modules, _ = self._artifacts()
        for index, state in enumerate(("idle", "terminal_failed", "aborted")):
            event = make_event("sample", self.worktree, state, "test",
                               f"2026-09-24T10:00:0{index}Z")
            result, _ = self._receive_event(event)
            self.assertNotEqual(result["state"], "eligible")
            self.assertTrue(modules.exists(), state)
        self.assertEqual(len((Path(self.tmp.name) / "logs/lifecycle-events.jsonl").read_text().splitlines()), 3)

    def test_canonical_success_event_runs_existing_process_and_lease_gates(self):
        modules, _ = self._artifacts()
        event = make_event("sample", self.worktree, "terminal_success", "exo",
                           "2026-09-24T10:20:00Z")
        active, _ = self._receive_event(event, [{"pid": 42, "cwd": self.worktree}])
        self.assertEqual((active["state"], active["reason"]), ("active", "process_uses_worktree"))
        self.assertTrue(modules.exists())

        lease = self.worktree / ".exo/locks/ticket.lock.json"
        lease.parent.mkdir(parents=True)
        lease.write_text(json.dumps({"expires_at": (dt.datetime.now(dt.timezone.utc)
                          + dt.timedelta(hours=1)).isoformat()}))
        leased, _ = self._receive_event(event)
        self.assertEqual(leased["reason"], "active_lease")
        self.assertTrue(modules.exists())

    def test_canonical_success_event_preserves_source_git_and_untracked_files(self):
        modules, _ = self._artifacts()
        notes = self.worktree / "notes.txt"
        notes.write_text("untracked work")
        head_before = self._git("rev-parse", "HEAD").stdout.strip()
        status_before = self._git("status", "--porcelain=v1", "--untracked-files=all").stdout
        event = make_event("sample", self.worktree, "terminal_success", "exo",
                           "2026-09-24T10:30:00Z")
        result, _ = self._receive_event(event)
        self.assertEqual(result["state"], "eligible")
        self.assertFalse(modules.exists())
        self.assertEqual((self.worktree / "src.js").read_text(), "keep source")
        self.assertEqual(notes.read_text(), "untracked work")
        self.assertEqual(self._git("rev-parse", "HEAD").stdout.strip(), head_before)
        self.assertEqual(self._git("status", "--porcelain=v1", "--untracked-files=all").stdout,
                         status_before)

    def test_duplicate_canonical_success_is_safe_noop(self):
        modules, _ = self._artifacts()
        event = make_event("sample", self.worktree, "terminal_success", "exo",
                           "2026-09-24T10:35:00Z")
        first, log = self._receive_event(event)
        second, _ = self._receive_event(event)
        self.assertEqual(first["state"], "eligible")
        self.assertTrue(first["event_recorded"])
        self.assertEqual((second["state"], second["reason"]),
                         ("skipped", "terminal_already_claimed"))
        self.assertFalse(second["event_recorded"])
        self.assertFalse(modules.exists())
        self.assertEqual(len(log.read_text().splitlines()), 1)

    def test_cleanup_failure_does_not_claim_terminal_and_retry_succeeds(self):
        modules, _ = self._artifacts()
        event = make_event("sample", self.worktree, "terminal_success", "exo",
                           "2026-09-24T10:35:30Z")
        with mock.patch.object(GC.shutil, "rmtree", side_effect=PermissionError("blocked")):
            failed, log = self._receive_event(event)
        claim = log.with_name("lifecycle-terminal-claims.jsonl")
        self.assertEqual((failed["state"], failed["reason"]),
                         ("unsafe", "cleanup_or_claim_failed"))
        self.assertTrue(modules.exists())
        self.assertFalse(claim.exists())

        retried, _ = self._receive_event(event)
        self.assertEqual(retried["state"], "eligible")
        self.assertFalse(modules.exists())
        self.assertTrue(claim.exists())

    def test_unmanaged_or_human_authored_session_cannot_be_collected(self):
        modules, _ = self._artifacts()
        for provenance in (None, "human-authored"):
            current = dict(self.manifest)
            if provenance is None:
                current.pop("provenance_type")
            else:
                current["provenance_type"] = provenance
            (self.sessions / "session-1.json").write_text(json.dumps(current))
            (self.worktree / ".agent-session/manifest.json").write_text(json.dumps(current))
            event = make_event("sample", self.worktree, "terminal_success", "exo",
                               "2026-09-24T10:35:45Z")
            result, _ = self._receive_event(event)
            self.assertNotEqual(result["state"], "eligible")
            self.assertTrue(modules.exists())

    def test_inconsistent_session_metadata_cannot_be_collected(self):
        modules, _ = self._artifacts()
        current = {**self.manifest, "task_id": "different-task"}
        (self.worktree / ".agent-session/manifest.json").write_text(json.dumps(current))
        event = make_event("sample", self.worktree, "terminal_success", "exo",
                           "2026-09-24T10:35:50Z")
        result, _ = self._receive_event(event)
        self.assertEqual((result["state"], result["reason"]),
                         ("unknown", "session_metadata_mismatch"))
        self.assertTrue(modules.exists())

    def test_terminal_replay_with_new_timestamp_cannot_clean_regenerated_dependencies(self):
        modules, _ = self._artifacts()
        first_event = make_event("sample", self.worktree, "terminal_success", "exo",
                                 "2026-09-24T10:36:00Z")
        first, _ = self._receive_event(first_event)
        self.assertEqual(first["state"], "eligible")
        modules.mkdir()
        (modules / "regenerated.bin").write_bytes(b"new dependency data")
        replay = make_event("sample", self.worktree, "terminal_success", "exo",
                            "2026-09-24T10:37:00Z")
        second, _ = self._receive_event(replay)
        self.assertEqual((second["state"], second["reason"]),
                         ("skipped", "terminal_already_claimed"))
        self.assertTrue((modules / "regenerated.bin").exists())

    def test_terminal_claim_survives_idle_state_for_same_session(self):
        modules, _ = self._artifacts()
        event = make_event("sample", self.worktree, "terminal_success", "exo",
                           "2026-09-24T10:37:15Z")
        first, _ = self._receive_event(event)
        self.assertEqual(first["state"], "eligible")
        modules.mkdir()
        (modules / "rebuilt.bin").write_bytes(b"same session regenerated data")
        idle = {**self.manifest, "lifecycle_state": "idle",
                "lifecycle_updated_at": "2026-09-24T10:40:00Z"}
        (self.sessions / "session-1.json").write_text(json.dumps(idle))
        (self.worktree / ".agent-session/manifest.json").write_text(json.dumps(idle))
        replay = {**event, "timestamp": "2026-09-24T10:40:30Z"}
        result, _ = self._receive_event(replay)
        self.assertEqual((result["state"], result["reason"]),
                         ("skipped", "terminal_already_claimed"))
        self.assertTrue((modules / "rebuilt.bin").exists())

    def test_real_process_scan_keeps_lifecycle_lock_outside_worktree(self):
        modules, _ = self._artifacts()
        event = make_event("sample", self.worktree, "terminal_success", "exo",
                           "2026-09-24T10:42:00Z")
        result, _ = self._receive_event(event, real_process_scan=True)
        self.assertEqual(result["state"], "eligible", result)
        self.assertFalse(modules.exists())
        self.assertEqual(list((self.worktree / ".agent-session").glob("gc.lock")), [])
        self.assertEqual(len(list((self.sessions / ".locks").glob("*.lock"))), 1)

    def test_old_terminal_event_cannot_finish_a_reopened_session(self):
        modules, _ = self._artifacts()
        event = make_event("sample", self.worktree, "terminal_success", "exo",
                           "2026-09-24T10:37:30Z")
        first, _ = self._receive_event(event)
        self.assertEqual(first["state"], "eligible")
        modules.mkdir()
        (modules / "rebuilt.bin").write_bytes(b"new session dependencies")

        reopened = {**self.manifest, "session_id": "session-2", "lifecycle_state": "active"}
        (self.sessions / "session-2.json").write_text(json.dumps(reopened))
        (self.worktree / ".agent-session/manifest.json").write_text(json.dumps(reopened))
        stale_replay = {**event, "timestamp": "2026-09-24T10:38:30Z"}
        with self.assertRaises(SystemExit):
            self._receive_event(stale_replay)
        self.assertTrue((modules / "rebuilt.bin").exists())

    def test_new_lease_during_final_recheck_stops_removal(self):
        modules, _ = self._artifacts()
        count = 0
        original_lease = GC.active_lease

        def lease_check(worktree, rows, now):
            nonlocal count
            count += 1
            if count == 2:
                lease = self.worktree / ".exo/locks/ticket.lock.json"
                lease.parent.mkdir(parents=True)
                lease.write_text(json.dumps({"expires_at": (dt.datetime.now(dt.timezone.utc)
                                  + dt.timedelta(hours=1)).isoformat()}))
            return original_lease(worktree, rows, now)

        event = make_event("sample", self.worktree, "terminal_success", "exo",
                           "2026-09-24T10:38:00Z")
        with mock.patch.object(GC, "active_lease", side_effect=lease_check):
            result, _ = self._receive_event(event)
        self.assertEqual((result["state"], result["reason"]),
                         ("active", "activity_changed_during_gc"))
        self.assertTrue(modules.exists())

    def test_event_task_mismatch_is_rejected_before_cleanup(self):
        modules, _ = self._artifacts()
        event = make_event("other-task", self.worktree, "terminal_success", "exo",
                           "2026-09-24T10:40:00Z")
        with self.assertRaises(SystemExit):
            self._receive_event(event)
        self.assertTrue(modules.exists())

    def test_cli_cannot_invent_terminal_success_without_canonical_event(self):
        argv = ["finish", "--config", str(ROOT / "agent-control/config/artifact-gc.json"),
                "--session-dir", str(self.sessions), "--worktree", str(self.worktree),
                "--bare", str(Path(self.tmp.name) / "unused.git"), "--task-root", str(self.safe),
                "--quarantine-root", str(Path(self.tmp.name) / "quarantine"),
                "--task-id", "sample", "--event-state", "terminal_success"]
        with self.assertRaises(SystemExit):
            GC.main(argv)

    def test_event_contract_requires_known_state_and_timezone(self):
        event = make_event("sample", self.worktree, "idle", "exo", "2026-09-24T10:50:00Z")
        self.assertEqual(validate_event(event), event)
        for bad in ({**event, "completion_state": "done"},
                    {**event, "timestamp": "2026-09-24T10:50:00"},
                    {key: value for key, value in event.items() if key != "session_id"}):
            with self.assertRaises(ValueError):
                validate_event(bad)


class ExoCompletionAdapterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.worktree = self.root / "task-worktree"
        self.worktree.mkdir()
        (self.worktree / ".agent-session").mkdir()
        (self.worktree / ".agent-session/manifest.json").write_text(json.dumps({
            "session_id": "agent-control-session-1", "task_id": "TASK-1",
            "worktree_path": str(self.worktree.resolve()), "lifecycle_state": "active"}))
        self.outside = self.root / "outside"
        self.outside.mkdir()
        self.calls = []
        self.exo_data = {"ticket_id": "TASK-1", "set_status": "done", "ticket_status": "done"}
        self.exo_rc = 0
        self.event_rc = 0

    def tearDown(self):
        self.tmp.cleanup()

    def runner(self, command, **kwargs):
        self.calls.append((command, kwargs))
        if command[0] == "fake-exo":
            stdout = json.dumps({"ok": True, "data": self.exo_data})
            return subprocess.CompletedProcess(command, self.exo_rc, stdout, "")
        return subprocess.CompletedProcess(command, self.event_rc, "event received\n", "")

    def run_adapter(self, args=None):
        return ADAPTER.run_exo_finish(
            project="portfolio-ops", task_id="TASK-1", worktree=self.worktree,
            args=args or ["--summary", "done", "--set-status", "done"],
            exo_command="fake-exo", agent_finish=self.root / "agent-finish",
            cwd=self.outside, runner=self.runner)

    def event(self):
        self.assertEqual(len(self.calls), 2)
        return json.loads(self.calls[1][1]["input"])

    def test_done_and_confirmed_success_emits_terminal_success(self):
        self.assertEqual(self.run_adapter(), 0)
        command = self.calls[0][0]
        self.assertEqual(command[:5], ["fake-exo", "--repo", str(self.worktree.resolve()),
                                       "--format", "json"])
        self.assertEqual(self.event()["completion_state"], "terminal_success")
        self.assertEqual(self.event()["source"], "exo")
        self.assertEqual(self.event()["session_id"], "agent-control-session-1")

    def test_done_command_failure_emits_failed_not_success(self):
        self.exo_rc = 1
        self.exo_data = {"ticket_id": "TASK-1", "set_status": "done", "ticket_status": None}
        self.assertEqual(self.run_adapter(), 1)
        self.assertEqual(self.event()["completion_state"], "terminal_failed")

    def test_keep_emits_idle_and_never_success(self):
        self.exo_data = {"ticket_id": "TASK-1", "set_status": "keep", "ticket_status": None}
        self.assertEqual(self.run_adapter(["--summary", "keep", "--set-status", "keep"]), 0)
        self.assertEqual(self.event()["completion_state"], "idle")

    def test_review_emits_idle_and_never_success(self):
        self.exo_data = {"ticket_id": "TASK-1", "set_status": "review", "ticket_status": "review"}
        self.assertEqual(self.run_adapter(["--summary", "review", "--set-status", "review"]), 0)
        self.assertEqual(self.event()["completion_state"], "idle")

    def test_unconfirmed_result_cannot_emit_success(self):
        self.exo_data = {"ticket_id": "TASK-1", "set_status": "review", "ticket_status": "review"}
        self.assertEqual(self.run_adapter(), 0)
        self.assertEqual(self.event()["completion_state"], "terminal_failed")

    def test_abort_emits_aborted_without_gc_success(self):
        def interrupt_on_exo(command, **kwargs):
            self.calls.append((command, kwargs))
            if command[0] == "fake-exo":
                raise KeyboardInterrupt
            return subprocess.CompletedProcess(command, 0, "event received\n", "")
        self.assertEqual(ADAPTER.run_exo_finish(
            project="portfolio-ops", task_id="TASK-1", worktree=self.worktree,
            args=["--summary", "done", "--set-status", "done"], exo_command="fake-exo",
            agent_finish=self.root / "agent-finish", cwd=self.outside, runner=interrupt_on_exo), 130)
        self.assertEqual(json.loads(self.calls[1][1]["input"])["completion_state"], "aborted")

    def test_event_delivery_failure_does_not_change_successful_exo_finish(self):
        self.event_rc = 1
        self.assertEqual(self.run_adapter(), 0)
        self.assertEqual(self.event()["completion_state"], "terminal_success")

    def test_requires_explicit_set_status_and_outside_cwd(self):
        with self.assertRaises(ValueError):
            self.run_adapter(["--summary", "missing status"])
        with self.assertRaises(ValueError):
            ADAPTER.run_exo_finish(
                project="portfolio-ops", task_id="TASK-1", worktree=self.worktree,
                args=["--summary", "done", "--set-status", "done"], exo_command="fake-exo",
                agent_finish=self.root / "agent-finish", cwd=self.worktree, runner=self.runner)
        self.assertEqual(self.calls, [])


class AgentControlProvenanceTests(unittest.TestCase):
    def test_temp_install_records_version_commit_and_install_time(self):
        with tempfile.TemporaryDirectory(prefix="agent-control-install-test-") as temporary:
            fixture = Path(temporary) / "source"
            fixture.mkdir()
            shutil.copytree(ROOT / "agent-control", fixture / "agent-control")
            (fixture / "scripts").mkdir()
            shutil.copy2(ROOT / "scripts/install-agent-control.sh",
                         fixture / "scripts/install-agent-control.sh")
            subprocess.run(["git", "init", "-q", str(fixture)], check=True)
            subprocess.run(["git", "-C", str(fixture), "config", "user.email",
                            "test@example.invalid"], check=True)
            subprocess.run(["git", "-C", str(fixture), "config", "user.name", "Test"], check=True)
            subprocess.run(["git", "-C", str(fixture), "add", "agent-control", "scripts"], check=True)
            subprocess.run(["git", "-C", str(fixture), "commit", "-qm", "clean fixture"], check=True)
            target = Path(temporary) / "agent-control"
            env = os.environ.copy()
            env["AGENT_CONTROL_ROOT"] = str(target)
            result = subprocess.run(
                ["bash", str(fixture / "scripts/install-agent-control.sh"), "--apply"],
                cwd=fixture, env=env, text=True, capture_output=True, check=False)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            provenance = json.loads((target / ".runtime-provenance.json").read_text(encoding="utf-8"))
            head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=fixture, check=True,
                                  text=True, capture_output=True).stdout.strip()
            version = (fixture / "agent-control/VERSION").read_text(encoding="utf-8").strip()
            self.assertEqual(provenance["runtime_version"], version)
            self.assertEqual(provenance["source_commit_sha"], head)
            self.assertEqual(len(provenance["source_commit_sha"]), 40)
            self.assertTrue(datetime.fromisoformat(provenance["installed_at"].replace("Z", "+00:00")).tzinfo)
            version_result = subprocess.run([str(target / "bin/agent-finish"), "--runtime-version"],
                                            text=True, capture_output=True, check=False, env=env)
            self.assertEqual(version_result.returncode, 0, version_result.stderr)
            self.assertEqual(json.loads(version_result.stdout), provenance)


if __name__ == "__main__":
    unittest.main()
