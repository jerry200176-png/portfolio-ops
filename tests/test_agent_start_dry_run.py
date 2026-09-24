import os
import subprocess
import tempfile
import unittest
from pathlib import Path


SOURCE_ROOT = Path(__file__).resolve().parents[1]


def run_git(*args, cwd=None):
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        text=True,
        capture_output=True,
    ).stdout.strip()


class AgentStartDryRunTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory(prefix="agent-start-dry-run-")
        self.root = Path(self.temp_dir.name)
        self.gateway = self.root / "gateway"
        self.bare = self.root / "repos" / "portfolio-ops.git"
        self.task_root = self.root / "tasks" / "portfolio-ops"
        self.control = self.root / "agent-control"
        self.sessions = self.control / "sessions"
        self.logs = self.control / "logs"
        for directory in (
            self.gateway / "bin",
            self.gateway / "lib",
            self.gateway / "schema",
            self.sessions,
            self.logs,
            self.bare.parent,
        ):
            directory.mkdir(parents=True, exist_ok=True)
        for relative in (
            "agent-control/VERSION",
            "agent-control/bin/agent-start",
            "agent-control/lib/common.sh",
            "agent-control/schema/session-manifest.schema.json",
        ):
            source = SOURCE_ROOT / relative
            target = self.gateway / relative.removeprefix("agent-control/")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(source.read_bytes())

        seed = self.root / "seed"
        seed.mkdir()
        run_git("init", "--initial-branch=main", cwd=seed)
        run_git("config", "user.name", "Audit Test", cwd=seed)
        run_git("config", "user.email", "audit@example.invalid", cwd=seed)
        (seed / "README.md").write_text("fixture\n", encoding="utf-8")
        run_git("add", "README.md", cwd=seed)
        run_git("commit", "-m", "fixture", cwd=seed)
        self.head = run_git("rev-parse", "HEAD", cwd=seed)
        run_git("init", "--bare", str(self.bare))
        run_git("push", str(self.bare), "main", cwd=seed)
        run_git(
            "--git-dir",
            str(self.bare),
            "update-ref",
            "refs/remotes/origin/main",
            self.head,
        )

        self.control.mkdir(parents=True, exist_ok=True)
        (self.sessions / "existing.json").write_text('{"session":"keep"}\n', encoding="utf-8")
        (self.logs / "launches.jsonl").write_text('{"launch":"keep"}\n', encoding="utf-8")
        metadata = self.control / "metadata"
        metadata.mkdir()
        (metadata / "lock.json").write_text('{"lock":"keep"}\n', encoding="utf-8")
        (metadata / "intent.json").write_text('{"intent":"keep"}\n', encoding="utf-8")

        self.env = os.environ.copy()
        self.env.update(
            {
                "AGENT_CONTROL_ROOT": str(self.control),
                "REPOS_ROOT": str(self.bare.parent),
                "TASKS_ROOT": str(self.task_root.parent),
            }
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def snapshot(self):
        ref_state = run_git(
            "--git-dir",
            str(self.bare),
            "for-each-ref",
            "--format=%(refname) %(objectname)",
        )
        worktrees = run_git("--git-dir", str(self.bare), "worktree", "list", "--porcelain")
        files = {}
        for directory in (self.control, self.task_root.parent):
            if not directory.exists():
                continue
            for path in sorted(directory.rglob("*")):
                if path.is_file():
                    files[str(path.relative_to(self.root))] = path.read_bytes()
        return {
            "refs": ref_state,
            "worktrees": worktrees,
            "task_root_exists": self.task_root.exists(),
            "files": files,
        }

    def invoke(self, task_id):
        return subprocess.run(
            [
                "bash",
                str(self.gateway / "bin/agent-start"),
                "portfolio-ops",
                task_id,
                "--dry-run",
            ],
            env=self.env,
            check=False,
            text=True,
            capture_output=True,
        )

    def test_dry_run_changes_no_git_or_session_state(self):
        before = self.snapshot()

        result = self.invoke("TKT-DRY-RUN-ISOLATION")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(f"base_sha={self.head}", result.stdout)
        self.assertIn("production_mutation=disabled", result.stdout)
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(run_git("--git-dir", str(self.bare), "rev-parse", "main"), self.head)

    def test_dry_run_without_cached_main_fails_without_state_changes(self):
        run_git(
            "--git-dir",
            str(self.bare),
            "update-ref",
            "-d",
            "refs/remotes/origin/main",
        )
        before = self.snapshot()

        result = self.invoke("TKT-DRY-RUN-NO-REMOTE-REF")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("dry-run requires cached refs/remotes/origin/main", result.stderr)
        self.assertEqual(self.snapshot(), before)


if __name__ == "__main__":
    unittest.main()
