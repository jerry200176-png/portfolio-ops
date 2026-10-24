#!/usr/bin/env python3
"""Delete one stale remote branch after verifying it through the GitHub API (RULEBOOK B5).

  python3 scripts/delete-merged-branch.py --repo <owner>/<name> --branch <name> [--dry-run]

Besides `gh pr merge --delete-branch`, this is the only way an agent may delete a remote
branch (RULEBOOK B5); the Bash hook denies every other shell-level deletion and allows this
command only in exactly this form. It reads through the REST API (`gh api`) and deletes exactly
one branch with an atomic compare-and-delete, only after verifying that:

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
- the ref still points at the verified tip when it is deleted: the delete is one GraphQL
  `updateRefs` call with `beforeOid` = the verified tip and an all-zero `afterOid`, which GitHub
  applies only if the ref has not moved (no read-then-delete race). The ref is re-read after.

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
ZERO_OID = "0" * 40
# Atomic compare-and-delete. A literal query (never read from a file); values are variables.
DELETE_MUTATION = (
    "mutation($repo: ID!, $name: GitRefname!, $before: GitObjectID!, $after: GitObjectID!) {"
    " updateRefs(input: {repositoryId: $repo, refUpdates: [{name: $name, beforeOid: $before,"
    " afterOid: $after}]}) { clientMutationId } }"
)
UPDATE_REFS_ACCEPT = "Accept: application/vnd.github.update-refs-preview+json"


class Refused(Exception):
    """The branch is not eligible for deletion."""


class ApiError(Exception):
    def __init__(self, message: str, not_found: bool = False):
        super().__init__(message)
        self.not_found = not_found


def run_gh(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(["gh", "api", *args], capture_output=True, text=True, check=False)


def api(path: str):
    """GET a REST path through `gh api`; raises ApiError (not_found on HTTP 404)."""
    out = run_gh(["-H", "Accept: application/vnd.github+json", path])
    if out.returncode != 0:
        err = (out.stderr or out.stdout).strip()
        raise ApiError(f"GET {path}: {err}", not_found="HTTP 404" in err)
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


def current_tip(repo: str, branch: str) -> str | None:
    """The branch's current tip, or None when refs/heads/<branch> no longer exists."""
    try:
        ref = api(f"repos/{repo}/git/ref/heads/{enc(branch)}")
    except ApiError as exc:
        if exc.not_found:
            return None
        raise
    return ((ref or {}).get("object") or {}).get("sha")


def compare_and_delete(repo: str, branch: str, tip: str, node_id: str) -> None:
    """Delete refs/heads/<branch> only if it still points at `tip` (GraphQL updateRefs)."""
    out = run_gh(["-H", UPDATE_REFS_ACCEPT, "graphql", "-f", f"query={DELETE_MUTATION}",
                  "-f", f"repo={node_id}", "-f", f"name=refs/heads/{branch}",
                  "-f", f"before={tip}", "-f", f"after={ZERO_OID}"])
    try:
        body = json.loads(out.stdout) if out.stdout.strip() else {}
    except ValueError:
        body = {}
    body = body if isinstance(body, dict) else {}
    errors = body.get("errors")
    failed = (out.returncode != 0 or bool(errors)
              or not isinstance((body.get("data") or {}).get("updateRefs"), dict))
    now = current_tip(repo, branch)
    if not failed and now is None:
        return
    if not failed:
        raise ApiError(f"updateRefs reported success but refs/heads/{branch} still exists at {now}")
    if now is not None and now != tip:
        raise Refused(f"refs/heads/{branch} changed to {now} after verification (verified "
                      f"{tip}); it was not deleted")
    detail = json.dumps(errors) if errors else (out.stderr or out.stdout).strip()
    if now is None:
        raise ApiError(f"updateRefs failed but refs/heads/{branch} is gone; check {repo}: {detail}")
    raise ApiError(f"updateRefs failed; refs/heads/{branch} is unchanged at {tip}: {detail}")


def pulls(repo: str, **query: str) -> list:
    result = api(f"repos/{repo}/pulls?" + urllib.parse.urlencode({**query, "per_page": "100"}))
    if not isinstance(result, list) or len(result) >= 100:
        raise Refused("too many pull requests to verify; check this branch by hand")
    return result


def verify(repo: str, branch: str) -> tuple[str, str, str]:
    """Return (tip_sha, reason, repo_node_id) when the branch may be deleted; raise Refused
    otherwise."""
    validate_names(repo, branch)
    info = api(f"repos/{repo}") or {}
    if info.get("fork") is not False:
        raise Refused(f"{repo} is a fork (or fork status is unknown): open PRs from this branch "
                      "into the upstream repository are not visible from the fork, so the "
                      "no-open-PR check cannot be done here; delete it by hand after checking "
                      "upstream")
    default, node_id = info.get("default_branch"), info.get("node_id")
    if not default or not node_id:
        raise Refused(f"could not read the default branch or node id of {repo}")
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
            return tip, f"tip is the head of {state} PR #{pr.get('number')}", node_id
    compare = api(f"repos/{repo}/compare/{enc(default)}...{tip}") or {}
    if compare.get("status") in ("behind", "identical"):
        return tip, f"tip is already in {default}", node_id
    raise Refused(f"tip {tip} is neither a merged/closed PR head nor in {default} "
                  f"(compare status {compare.get('status')!r}); it may hold unmerged work")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0], allow_abbrev=False)
    parser.add_argument("--repo", required=True, help="<owner>/<name>")
    parser.add_argument("--branch", required=True, help="branch name, without refs/heads/")
    parser.add_argument("--dry-run", action="store_true", help="verify only; do not delete")
    args = parser.parse_args(argv)
    try:
        tip, reason, node_id = verify(args.repo, args.branch)
        if not args.dry_run:
            compare_and_delete(args.repo, args.branch, tip, node_id)
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
