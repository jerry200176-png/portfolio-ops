import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
import datetime as dt
import shutil
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("artifact_gc", ROOT / "agent-control/lib/artifact_gc.py")
GC = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GC)


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
        (self.worktree / ".gitignore").write_text("node_modules/\n.next/\n")
        (self.worktree / "package.json").write_text(json.dumps({
            "scripts": {"build": "next build"}, "dependencies": {"next": "1.0.0"}
        }))
        (self.worktree / "package-lock.json").write_text("{}")
        (self.worktree / "src.js").write_text("keep source")
        self._git("add", ".gitignore", "package.json", "package-lock.json", "src.js")
        self._git("commit", "-qm", "fixture")
        self.manifest = {"session_id": "session-1", "task_id": "sample",
                         "worktree_path": str(self.worktree)}
        (self.sessions / "session-1.json").write_text(json.dumps(self.manifest))
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

    def test_terminal_dirty_source_keeps_source_but_reclaims_locked_artifacts(self):
        modules, build = self._artifacts()
        user_file = self.worktree / "notes.txt"
        user_file.write_text("untracked work")
        result = self._evaluate(terminal_signal=True)
        self.assertEqual(result["state"], "eligible")
        self.assertEqual({a["kind"] for a in result["artifacts"]}, {"node_modules", ".next"})
        with mock.patch.object(GC, "process_snapshot", return_value=([], True)):
            collected = self._evaluate(terminal_signal=True, dry_run=False)
        self.assertTrue(collected["state"] == "eligible")
        self.assertFalse(modules.exists())
        self.assertFalse(build.exists())
        self.assertEqual((self.worktree / "src.js").read_text(), "keep source")
        self.assertEqual(user_file.read_text(), "untracked work")
        self.assertTrue(self.worktree.exists())

    def test_active_process_cwd_blocks_collection(self):
        self._artifacts()
        result = GC.evaluate(self.worktree, self.sessions, self.policy, [self.safe],
                             [{"pid": 42, "cwd": self.worktree}], True, terminal_signal=True)
        self.assertEqual((result["state"], result["reason"]), ("active", "process_uses_worktree"))

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

    def test_tracked_next_output_is_never_removed(self):
        _, build = self._artifacts()
        (build / "tracked.js").write_text("deliverable")
        self._git("add", "-f", ".next/tracked.js")
        result = self._evaluate(terminal_signal=True)
        self.assertFalse(any(a["kind"] == ".next" for a in result["artifacts"]))
        self.assertIn("tracked_content", [r["reason"] for r in result["skipped_artifacts"]])

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

    def test_cli_shutdown_marks_session_idle_and_keeps_task_tree(self):
        self.assertTrue((ROOT / "agent-control/bin/agent-finish").stat().st_mode & 0o111)
        modules, _ = self._artifacts()
        with mock.patch.object(GC, "process_snapshot", return_value=([], True)):
            result = self._evaluate(terminal_signal=True, lifecycle_state="idle", dry_run=False)
        manifest = json.loads((self.sessions / "session-1.json").read_text())
        self.assertEqual(manifest["lifecycle_state"], "idle")
        self.assertTrue(manifest["lifecycle_updated_at"])
        self.assertFalse(modules.exists())
        self.assertTrue(self.worktree.exists())
        self.assertEqual(result["state"], "eligible")

    def test_capacity_limits_are_configured_not_duplicated(self):
        changed = {**self.policy, "capacity_gib": {"pressure_below": 70, "critical_below": 40}}
        self.assertEqual(GC.pressure(changed, 75 * 1024**3), "NORMAL")
        self.assertEqual(GC.pressure(changed, 55 * 1024**3), "PRESSURE")
        self.assertEqual(GC.pressure(changed, 35 * 1024**3), "CRITICAL")


if __name__ == "__main__":
    unittest.main()
