"""scripts/delete-merged-branch.py with a mocked `gh api` (no network)."""
import importlib.util
import io
import json
import subprocess
import unittest
import urllib.parse
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("dmb", ROOT / "scripts/delete-merged-branch.py")
dmb = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(dmb)

TIP = "a" * 40
REPO, BRANCH = "o/r", "chore/old-x"


class FakeGh:
    """Routes `gh api` calls to canned responses and records them."""

    def __init__(self, **overrides):
        self.calls = []
        self.state = {
            "default": "main",
            "tips": [TIP],  # successive answers for git/ref/heads/<branch>
            "protected": False,
            "rules": [],
            "open_head": [],
            "open_base": [],
            "closed": [{"number": 7, "merged_at": "2026-10-01T00:00:00Z",
                        "head": {"sha": TIP, "ref": BRANCH, "repo": {"full_name": REPO}}}],
            "compare": "diverged",
            "fail": {},  # path prefix -> stderr, returned with exit code 1
        }
        self.state.update(overrides)

    def __call__(self, args):
        method = args[args.index("-X") + 1] if "-X" in args else "GET"
        path = args[-1]
        self.calls.append((method, path))
        for prefix, err in self.state["fail"].items():
            if path.startswith(prefix):
                return subprocess.CompletedProcess(args, 1, "", err)
        return subprocess.CompletedProcess(args, 0, json.dumps(self.route(method, path)), "")

    def route(self, method, path):
        s, enc = self.state, dmb.enc(BRANCH)
        base, _, query = path.partition("?")
        q = dict(urllib.parse.parse_qsl(query))
        if method == "DELETE":
            assert base == f"repos/{REPO}/git/refs/heads/{enc}", base
            return None
        if base == f"repos/{REPO}":
            return {"default_branch": s["default"]}
        if base == f"repos/{REPO}/git/ref/heads/{enc}":
            sha = s["tips"].pop(0) if len(s["tips"]) > 1 else s["tips"][0]
            return {"ref": f"refs/heads/{BRANCH}", "object": {"type": "commit", "sha": sha}}
        if base == f"repos/{REPO}/branches/{enc}":
            return {"protected": s["protected"]}
        if base == f"repos/{REPO}/rules/branches/{enc}":
            return s["rules"]
        if base == f"repos/{REPO}/pulls":
            if q["state"] == "open":
                return s["open_head"] if "head" in q else s["open_base"]
            return s["closed"]
        if base.startswith(f"repos/{REPO}/compare/"):
            return {"status": s["compare"]}
        raise AssertionError(f"unexpected call {method} {path}")


class DeleteMergedBranchTests(unittest.TestCase):
    def run_main(self, fake, argv=None):
        original = dmb.run_gh
        dmb.run_gh = fake
        out, err = io.StringIO(), io.StringIO()
        try:
            with redirect_stdout(out), redirect_stderr(err):
                code = dmb.main(argv or ["--repo", REPO, "--branch", BRANCH])
        finally:
            dmb.run_gh = original
        return code, out.getvalue(), err.getvalue()

    def deletes(self, fake):
        return [c for c in fake.calls if c[0] == "DELETE"]

    def test_deletes_branch_whose_tip_is_a_merged_pr_head(self):
        fake = FakeGh()
        code, out, _ = self.run_main(fake)
        self.assertEqual(code, 0)
        self.assertEqual(self.deletes(fake), [("DELETE", f"repos/{REPO}/git/refs/heads/chore/old-x")])
        self.assertIn(f"tip={TIP}", out)
        self.assertIn("merged PR #7", out)
        self.assertIn(f"git push origin {TIP}:refs/heads/{BRANCH}", out)

    def test_deletes_branch_whose_tip_is_already_in_the_default_branch(self):
        for status in ("behind", "identical"):
            fake = FakeGh(closed=[], compare=status)
            code, out, _ = self.run_main(fake)
            self.assertEqual(code, 0, status)
            self.assertEqual(len(self.deletes(fake)), 1)
            self.assertIn("already in main", out)

    def test_dry_run_verifies_but_never_deletes(self):
        fake = FakeGh()
        code, out, _ = self.run_main(fake, ["--repo", REPO, "--branch", BRANCH, "--dry-run"])
        self.assertEqual(code, 0)
        self.assertEqual(self.deletes(fake), [])
        self.assertIn("eligible (dry run", out)

    def test_refuses_unsafe_names_before_any_api_call(self):
        for name in ("main", "Master", "HEAD", "trunk", "develop", "gh-pages", "release",
                     "release/1.2", "releases/x", "Release-2026", "hotfix/y", "hotfix-1",
                     "a..b", "x.lock", "-x", "x/", "a//b", "a/.b", "refs/heads/x", "a b",
                     "$(x)", "old#1", "@", "x@{1}"):
            fake = FakeGh()
            code, _, err = self.run_main(fake, ["--repo", REPO, f"--branch={name}"])
            self.assertEqual(code, 2, name)
            self.assertEqual(fake.calls, [], name)
            self.assertIn("refused", err)
        for repo in ("o", "o/r/x", "../r", "o/..", "o/r;x"):
            fake = FakeGh()
            code, _, _ = self.run_main(fake, ["--repo", repo, "--branch", BRANCH])
            self.assertEqual(code, 2, repo)
            self.assertEqual(fake.calls, [], repo)

    def test_refuses_each_failed_api_check_without_deleting(self):
        cases = {
            "default branch": {"default": BRANCH},
            "protected": {"protected": True},
            "protection unknown": {"protected": None},
            "deletion rule": {"rules": [{"type": "deletion"}]},
            "update rule": {"rules": [{"type": "update"}, {"type": "pull_request"}]},
            "open PR from it": {"open_head": [{"number": 9}]},
            "open PR into it": {"open_base": [{"number": 9}]},
            "unmerged tip": {"closed": [{"number": 7, "merged_at": None, "head": {
                "sha": "b" * 40, "ref": BRANCH, "repo": {"full_name": REPO}}}], "compare": "ahead"},
            "PR from a fork": {"closed": [{"number": 7, "merged_at": "x", "head": {
                "sha": TIP, "ref": BRANCH, "repo": {"full_name": "fork/r"}}}], "compare": "diverged"},
            "tip moved": {"tips": [TIP, "c" * 40]},
            "missing branch": {"fail": {f"repos/{REPO}/git/ref/": "gh: Not Found (HTTP 404)"}},
        }
        for label, overrides in cases.items():
            fake = FakeGh(**overrides)
            code, _, err = self.run_main(fake)
            self.assertEqual(code, 2, f"{label}: {err}")
            self.assertEqual(self.deletes(fake), [], label)

    def test_rules_that_do_not_block_deletion_are_allowed(self):
        fake = FakeGh(rules=[{"type": "pull_request"}, {"type": "required_status_checks"}])
        self.assertEqual(self.run_main(fake)[0], 0)
        self.assertTrue(dmb.BLOCKING_RULES >= {"deletion", "update"})

    def test_api_errors_exit_1_without_deleting(self):
        fake = FakeGh(fail={f"repos/{REPO}/branches/": "gh: Server Error (HTTP 500)"})
        code, _, err = self.run_main(fake)
        self.assertEqual(code, 1)
        self.assertIn("error", err)
        self.assertEqual(self.deletes(fake), [])

    def test_encodes_each_segment_and_rejects_abbreviated_options(self):
        self.assertEqual(dmb.enc("a b/c%d"), "a%20b/c%25d")
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            dmb.main(["--rep", REPO, "--branch", BRANCH])


if __name__ == "__main__":
    unittest.main()
