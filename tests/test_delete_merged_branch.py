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
NODE_ID = "R_kgTEST"


class FakeGh:
    """A fake `gh api`: REST GETs from canned state, and a GraphQL `updateRefs`
    that, like GitHub, deletes the ref only if it still points at beforeOid."""

    def __init__(self, repo=REPO, **overrides):
        self.calls, self.repo = [], repo
        self.state = {
            "default": "main",
            "fork": False,
            "remote_tip": TIP,
            "moved_to": None,  # a push that lands after verification, before the delete
            "graphql_error": None,  # e.g. a permission error from updateRefs
            "graphql_noop": False,  # updateRefs reports success but changes nothing
            "deleted": False,
            "protected": False,
            "rules": [],
            "open_head": [],
            "open_base": [],
            "closed": [{"number": 7, "merged_at": "2026-10-01T00:00:00Z",
                        "head": {"sha": TIP, "ref": BRANCH, "repo": {"full_name": repo}}}],
            "compare": "diverged",
            "fail": {},  # REST path prefix -> stderr, returned with exit code 1
        }
        self.state.update(overrides)

    def __call__(self, args):
        if "graphql" in args:
            return self.graphql(args)
        assert "-X" not in args, f"REST write attempted: {args}"
        path = args[-1]
        self.calls.append(("GET", path))
        for prefix, err in self.state["fail"].items():
            if path.startswith(prefix):
                return subprocess.CompletedProcess(args, 1, "", err)
        if self.state["deleted"] and path.startswith(f"repos/{self.repo}/git/ref/heads/"):
            return subprocess.CompletedProcess(args, 1, "", "gh: Not Found (HTTP 404)")
        return subprocess.CompletedProcess(args, 0, json.dumps(self.route(path)), "")

    def graphql(self, args):
        fields = dict(args[i + 1].split("=", 1) for i, a in enumerate(args) if a == "-f")
        self.calls.append(("GRAPHQL", fields))
        s = self.state
        if s["moved_to"]:
            s["remote_tip"] = s["moved_to"]
        if s["graphql_error"]:
            body = {"errors": [{"message": s["graphql_error"]}]}
            return subprocess.CompletedProcess(args, 1, json.dumps(body), "gh: " + s["graphql_error"])
        if fields["before"] != s["remote_tip"]:
            msg = f"Reference {fields['name']} is at {s['remote_tip']}, expected {fields['before']}"
            return subprocess.CompletedProcess(args, 1, json.dumps({"errors": [{"message": msg}]}),
                                               "gh: " + msg)
        if fields["after"] == "0" * 40 and not s["graphql_noop"]:
            s["deleted"] = True
        return subprocess.CompletedProcess(
            args, 0, json.dumps({"data": {"updateRefs": {"clientMutationId": None}}}), "")

    def route(self, path):
        s, enc, repo = self.state, dmb.enc(BRANCH), self.repo
        base, _, query = path.partition("?")
        q = dict(urllib.parse.parse_qsl(query))
        if base == f"repos/{repo}":
            return {"default_branch": s["default"], "fork": s["fork"], "node_id": NODE_ID}
        if base == f"repos/{repo}/git/ref/heads/{enc}":
            return {"ref": f"refs/heads/{BRANCH}",
                    "object": {"type": "commit", "sha": s["remote_tip"]}}
        if base == f"repos/{repo}/branches/{enc}":
            return {"protected": s["protected"]}
        if base == f"repos/{repo}/rules/branches/{enc}":
            return s["rules"]
        if base == f"repos/{repo}/pulls":
            if q["state"] == "open":
                return s["open_head"] if "head" in q else s["open_base"]
            return s["closed"]
        if base.startswith(f"repos/{repo}/compare/"):
            return {"status": s["compare"]}
        raise AssertionError(f"unexpected call GET {path}")


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
        return [c[1] for c in fake.calls if c[0] == "GRAPHQL"]

    def test_deletes_with_an_atomic_compare_and_delete(self):
        fake = FakeGh()
        code, out, _ = self.run_main(fake)
        self.assertEqual(code, 0)
        (fields,) = self.deletes(fake)
        self.assertTrue(fields["query"].startswith("mutation("))
        self.assertIn("updateRefs", fields["query"])
        self.assertEqual(fields, {"query": dmb.DELETE_MUTATION, "repo": NODE_ID,
                                  "name": f"refs/heads/{BRANCH}", "before": TIP, "after": "0" * 40})
        self.assertTrue(fake.state["deleted"])
        # The ref is re-read after the mutation to confirm it is gone.
        self.assertEqual(fake.calls[-1], ("GET", f"repos/{REPO}/git/ref/heads/{dmb.enc(BRANCH)}"))
        self.assertIn(f"tip={TIP}", out)
        self.assertIn("merged PR #7", out)
        self.assertIn(f"gh api -X POST repos/{REPO}/git/refs -f ref=refs/heads/{BRANCH} "
                      f"-f sha={TIP}", out)
        self.assertNotIn("git push origin", out)

    def test_tip_moved_before_the_delete_is_not_deleted(self):
        fake = FakeGh(moved_to="c" * 40)
        code, out, err = self.run_main(fake)
        self.assertEqual(code, 2)
        self.assertFalse(fake.state["deleted"])
        self.assertIn(f"changed to {'c' * 40}", err)
        self.assertIn("not deleted", err)
        self.assertEqual(out, "")

    def test_graphql_error_exits_1_and_leaves_the_branch(self):
        fake = FakeGh(graphql_error="Resource not accessible by integration")
        code, out, err = self.run_main(fake)
        self.assertEqual(code, 1)
        self.assertFalse(fake.state["deleted"])
        self.assertIn("Resource not accessible by integration", err)
        self.assertIn("unchanged", err)
        self.assertEqual(out, "")

    def test_reported_success_with_the_ref_still_present_is_an_error(self):
        fake = FakeGh(graphql_noop=True)
        code, out, err = self.run_main(fake)
        self.assertEqual(code, 1)
        self.assertIn("still exists", err)
        self.assertEqual(out, "")

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
            "fork": {"fork": True},
            "fork status unknown": {"fork": None},
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

    def test_refuses_forks_and_says_why(self):
        fake = FakeGh(fork=True)
        code, _, err = self.run_main(fake)
        self.assertEqual(code, 2)
        self.assertIn("is a fork", err)
        self.assertIn("upstream", err)
        self.assertEqual(self.deletes(fake), [])
        self.assertEqual(fake.calls, [("GET", f"repos/{REPO}")])

    def test_restore_command_targets_the_requested_repo(self):
        for repo in ("o/r", "other-owner/other.repo"):
            fake = FakeGh(repo=repo)
            code, out, _ = self.run_main(fake, ["--repo", repo, "--branch", BRANCH])
            self.assertEqual(code, 0, repo)
            self.assertIn(f"restore: gh api -X POST repos/{repo}/git/refs "
                          f"-f ref=refs/heads/{BRANCH} -f sha={TIP}", out)
            self.assertTrue(fake.state["deleted"], repo)


if __name__ == "__main__":
    unittest.main()
