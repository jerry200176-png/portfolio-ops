#!/usr/bin/env python3
"""Delete one stale remote branch after verifying it through the GitHub API (RULEBOOK B5).

  python3 scripts/delete-merged-branch.py --repo <owner>/<name> --branch <name> [--dry-run]

Besides `gh pr merge --delete-branch`, this is the only way an agent may delete a remote
branch (RULEBOOK B5); the Bash hook denies every other shell-level deletion and allows this
command only in exactly this form. It uses the REST API through `gh api` and deletes exactly
one branch, only after verifying that:

- the repo and branch are plain names and the branch passes `git check-ref-format --branch`;
- the repo is not a fork (upstream PRs from a fork's branch are not visible from the fork);
- the branch is not the default branch, HEAD, main, master, trunk, develop, gh-pages,
  release*, releases/* or hotfix*, and refs/heads/<branch> exists (it is a branch, not a tag);
- GitHub reports it unprotected (`branches/<b>.protected` is false) and no ruleset rule of
  type `deletion` or `update` applies to it (`rules/branches/<b>`);
- no open PR has it as head or base;
- its tip SHA is the head SHA of a merged or closed PR from it (the PR's "Restore branch"
  button brings it back), or the tip is already in the default branch
  (`compare/<default>...<tip>` is `behind` or `identical`);
- the tip has not moved between the checks and the delete.

It prints the repo, branch, tip SHA and a restore command that targets --repo explicitly
(`gh api -X POST repos/<repo>/git/refs ...`) for the session checkpoint.
Exit codes: 0 deleted (or eligible with --dry-run), 2 refused, 1 API or tool error.
Stdlib only; needs `gh` (authenticated) and `git` on PATH.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import urllib.parse

REPO_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,99}/[A-Za-z0-9][A-Za-z0-9_.-]{0,99}")
BRANCH_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._/-]{0,199}")
PROTECTED_RE = re.compile(
    r"^(?:head|main|master|trunk|develop|gh-pages|"
    r"(?:releases?|hotfix(?:es)?)(?:[/_.-].*)?)$",
    re.I,
)
BLOCKING_RULES = {"deletion", "update"}


class Refused(Exception):
    """The branch is not eligible for deletion."""


class ApiError(Exception):
    def __init__(self, message: str, not_found: bool = False):
        super().__init__(message)
        self.not_found = not_found


def run_gh(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(["gh", "api", *args], capture_output=True, text=True, check=False)


def api(path: str, method: str = "GET"):
    args = ["-H", "Accept: application/vnd.github+json"]
    if method != "GET":
        args += ["-X", method]
    out = run_gh(args + [path])
    if out.returncode != 0:
        err = (out.stderr or out.stdout).strip()
        raise ApiError(f"{method} {path}: {err}", not_found="HTTP 404" in err)
    text = out.stdout.strip()
    return json.loads(text) if text else None


def enc(name: str) -> str:
    """URL-encode a ref name segment by segment (slashes stay path separators)."""
    return "/".join(urllib.parse.quote(seg, safe="") for seg in name.split("/"))


def validate_names(repo: str, branch: str) -> None:
    if not REPO_RE.fullmatch(repo) or ".." in repo:
        raise Refused(f"repo {repo!r} is not a plain <owner>/<name>")
    if (not BRANCH_RE.fullmatch(branch) or ".." in branch or "//" in branch
            or branch.endswith(("/", ".", ".lock")) or "/." in branch
            or branch.startswith("refs/")):
        raise Refused(f"branch {branch!r} is not a plain branch name")
    check = subprocess.run(["git", "check-ref-format", "--branch", branch],
                           capture_output=True, text=True, check=False)
    if check.returncode != 0 or check.stdout.strip() != branch:
        raise Refused(f"branch {branch!r} fails git check-ref-format --branch")
    if PROTECTED_RE.match(branch):
        raise Refused(f"branch {branch!r} is a default, protected, release or hotfix name")


def tip_of(repo: str, branch: str) -> str:
    try:
        ref = api(f"repos/{repo}/git/ref/heads/{enc(branch)}")
    except ApiError as exc:
        if exc.not_found:
            raise Refused(f"refs/heads/{branch} does not exist in {repo}") from exc
        raise
    if (not isinstance(ref, dict) or ref.get("ref") != f"refs/heads/{branch}"
            or (ref.get("object") or {}).get("type") != "commit"):
        raise Refused(f"refs/heads/{branch} is not a branch pointing at a commit")
    return ref["object"]["sha"]


def pulls(repo: str, **query: str) -> list:
    result = api(f"repos/{repo}/pulls?" + urllib.parse.urlencode({**query, "per_page": "100"}))
    if not isinstance(result, list) or len(result) >= 100:
        raise Refused("too many pull requests to verify; check this branch by hand")
    return result


def verify(repo: str, branch: str) -> tuple[str, str]:
    """Return (tip_sha, reason) when the branch may be deleted; raise Refused otherwise."""
    validate_names(repo, branch)
    info = api(f"repos/{repo}") or {}
    if info.get("fork") is not False:
        raise Refused(f"{repo} is a fork (or fork status is unknown): open PRs from this branch "
                      "into the upstream repository are not visible from the fork, so the "
                      "no-open-PR check cannot be done here; delete it by hand after checking "
                      "upstream")
    default = info.get("default_branch")
    if not default:
        raise Refused(f"could not read the default branch of {repo}")
    if branch == default:
        raise Refused(f"{branch!r} is the default branch of {repo}")
    tip = tip_of(repo, branch)
    if (api(f"repos/{repo}/branches/{enc(branch)}") or {}).get("protected") is not False:
        raise Refused(f"{branch!r} is protected (or protection is unknown)")
    rules = api(f"repos/{repo}/rules/branches/{enc(branch)}")
    if not isinstance(rules, list):
        raise Refused("could not read the ruleset rules for this branch")
    blocking = sorted({r.get("type") for r in rules if r.get("type") in BLOCKING_RULES})
    if blocking:
        raise Refused(f"ruleset rules {blocking} apply to {branch!r}")
    owner = repo.split("/")[0]
    if pulls(repo, state="open", head=f"{owner}:{branch}"):
        raise Refused(f"{branch!r} is the head of an open PR")
    if pulls(repo, state="open", base=branch):
        raise Refused(f"{branch!r} is the base of an open PR")
    for pr in pulls(repo, state="closed", head=f"{owner}:{branch}"):
        head = pr.get("head") or {}
        head_repo = (head.get("repo") or {}).get("full_name")
        if head.get("sha") == tip and head.get("ref") == branch and head_repo in (None, repo):
            state = "merged" if pr.get("merged_at") else "closed"
            return tip, f"tip is the head of {state} PR #{pr.get('number')}"
    compare = api(f"repos/{repo}/compare/{enc(default)}...{tip}") or {}
    if compare.get("status") in ("behind", "identical"):
        return tip, f"tip is already in {default}"
    raise Refused(f"tip {tip} is neither a merged/closed PR head nor in {default} "
                  f"(compare status {compare.get('status')!r}); it may hold unmerged work")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0], allow_abbrev=False)
    parser.add_argument("--repo", required=True, help="<owner>/<name>")
    parser.add_argument("--branch", required=True, help="branch name, without refs/heads/")
    parser.add_argument("--dry-run", action="store_true", help="verify only; do not delete")
    args = parser.parse_args(argv)
    try:
        tip, reason = verify(args.repo, args.branch)
        if tip_of(args.repo, args.branch) != tip:
            raise Refused("the branch moved during verification; re-run")
        if not args.dry_run:
            api(f"repos/{args.repo}/git/refs/heads/{enc(args.branch)}", method="DELETE")
    except Refused as exc:
        print(f"refused: repo={args.repo} branch={args.branch}: {exc}", file=sys.stderr)
        return 2
    except (ApiError, OSError, ValueError) as exc:
        print(f"error: repo={args.repo} branch={args.branch}: {exc}", file=sys.stderr)
        return 1
    verb = "eligible (dry run, nothing deleted)" if args.dry_run else "deleted"
    print(f"{verb}: repo={args.repo} branch={args.branch} tip={tip} ({reason})")
    print(f"restore: gh api -X POST repos/{args.repo}/git/refs "
          f"-f ref=refs/heads/{args.branch} -f sha={tip}  (or the PR's \"Restore branch\" button)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
