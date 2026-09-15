"""Allowlisted GitHub PR mutations (Effect Journal only).

Never wraps deploy / workflow_dispatch / issue close.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from typing import Any, Optional, Protocol

from .effect_allowlist import assert_effect_allowed


class MutationError(RuntimeError):
    blocker = "effect_mutation_failed"


class GitHubMutator(Protocol):
    def pr_create(self, *, repo: str, title: str, body: str, head: str, base: str = "main") -> dict[str, Any]: ...
    def pr_comment(self, *, repo: str, pr_number: int, body: str) -> dict[str, Any]: ...
    def pr_merge(self, *, repo: str, pr_number: int, method: str = "squash") -> dict[str, Any]: ...


@dataclass
class GhCliMutator:
    gh_bin: str = "gh"
    timeout_sec: float = 120.0

    def _run(self, args: list[str]) -> str:
        forbidden = {
            "workflow", "run", "deploy", "delete", "close", "lock", "unlock",
            "edit", "ready",  # keep surface small; comment/create/merge only
        }
        # Allow: pr create | pr comment | pr merge | pr view (for post-check)
        if args and args[0] == "pr" and len(args) > 1 and args[1] in ("create", "comment", "merge", "view"):
            pass
        else:
            for a in args:
                if a in forbidden:
                    raise MutationError(f"mutation verb refused: {a}")
        proc = subprocess.run(
            [self.gh_bin, *args],
            capture_output=True,
            text=True,
            timeout=self.timeout_sec,
            check=False,
        )
        if proc.returncode != 0:
            raise MutationError((proc.stderr or proc.stdout or "gh failed").strip())
        return proc.stdout

    def pr_create(self, *, repo: str, title: str, body: str, head: str, base: str = "main") -> dict[str, Any]:
        assert_effect_allowed(action="github_pr_create", repo=repo)
        out = self._run([
            "pr", "create", "--repo", repo, "--title", title, "--body", body,
            "--head", head, "--base", base,
        ])
        # gh prints URL; resolve number via view
        view = self._run([
            "pr", "view", "--repo", repo, "--head", head,
            "--json", "number,url,headRefOid,state",
        ])
        data = json.loads(view)
        data["create_stdout"] = out.strip()
        return data

    def pr_comment(self, *, repo: str, pr_number: int, body: str) -> dict[str, Any]:
        assert_effect_allowed(action="github_pr_comment", repo=repo)
        out = self._run(["pr", "comment", str(pr_number), "--repo", repo, "--body", body])
        return {"pr": pr_number, "comment_stdout": out.strip()}

    def pr_merge(self, *, repo: str, pr_number: int, method: str = "squash") -> dict[str, Any]:
        assert_effect_allowed(action="github_pr_merge", repo=repo)
        args = ["pr", "merge", str(pr_number), "--repo", repo]
        if method == "squash":
            args.append("--squash")
        elif method == "merge":
            args.append("--merge")
        elif method == "rebase":
            args.append("--rebase")
        else:
            raise MutationError(f"unsupported merge method: {method}")
        args.append("--delete-branch")
        out = self._run(args)
        view = self._run([
            "pr", "view", str(pr_number), "--repo", repo,
            "--json", "number,url,state,mergedAt,mergeCommit,headRefOid",
        ])
        data = json.loads(view)
        data["merge_stdout"] = out.strip()
        return data


@dataclass
class FakeGitHubMutator:
    """In-memory mutator for unit tests."""

    created: list[dict[str, Any]] = None  # type: ignore
    comments: list[dict[str, Any]] = None  # type: ignore
    merges: list[dict[str, Any]] = None  # type: ignore
    next_pr: int = 1000
    fail_merge: bool = False
    merge_ambiguous: bool = False

    def __post_init__(self) -> None:
        self.created = [] if self.created is None else self.created
        self.comments = [] if self.comments is None else self.comments
        self.merges = [] if self.merges is None else self.merges

    def pr_create(self, *, repo: str, title: str, body: str, head: str, base: str = "main") -> dict[str, Any]:
        assert_effect_allowed(action="github_pr_create", repo=repo)
        self.next_pr += 1
        data = {
            "number": self.next_pr,
            "url": f"https://example.invalid/{repo}/pull/{self.next_pr}",
            "headRefOid": "d" * 40,
            "state": "OPEN",
            "head": head,
            "base": base,
            "title": title,
            "body": body,
        }
        self.created.append(data)
        return data

    def pr_comment(self, *, repo: str, pr_number: int, body: str) -> dict[str, Any]:
        assert_effect_allowed(action="github_pr_comment", repo=repo)
        data = {"pr": pr_number, "body": body, "repo": repo}
        self.comments.append(data)
        return data

    def pr_merge(self, *, repo: str, pr_number: int, method: str = "squash") -> dict[str, Any]:
        assert_effect_allowed(action="github_pr_merge", repo=repo)
        if self.fail_merge:
            raise MutationError("fake merge failed")
        if self.merge_ambiguous:
            raise MutationError("HTTP 502 ambiguous")
        data = {
            "number": pr_number,
            "url": f"https://example.invalid/{repo}/pull/{pr_number}",
            "state": "MERGED",
            "mergedAt": "2026-09-15T00:00:00Z",
            "mergeCommit": {"oid": "e" * 40},
            "headRefOid": "d" * 40,
            "method": method,
        }
        self.merges.append(data)
        return data
