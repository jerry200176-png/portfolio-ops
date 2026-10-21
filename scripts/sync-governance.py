#!/usr/bin/env python3
"""Open rulebook sync PRs in every repo registered with governance_sync: true in portfolio.yaml.

Copybara-style: the source of truth is this repo at one commit; each target gets the vendored
rulebook (via its own `check-rulebook.py --update`, so the lock hash stays correct), the sync
script, and the governance skills, on a new branch + PR. Stdlib + pyyaml. Never force-pushes.

  python3 scripts/sync-governance.py --sha <40-hex> [--dry-run] [--only owner/repo]

Needs env GOVERNANCE_SYNC_TOKEN (fine-grained PAT, see docs/governance-sync.md); without it the
script prints a notice and exits 0.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SYNC_FILES = ["scripts/check-rulebook.py",
              ".claude/skills/reference-first-design/SKILL.md",
              ".claude/skills/product-design-doc/SKILL.md"]
TEMPLATE_SRC = "governance/templates/pull_request_template.md"
TEMPLATE_DST = ".github/PULL_REQUEST_TEMPLATE.md"
MARKERS = ("參考做法", "設計文件", "重複檢查")
BRANCH_PREFIX = "chore/rulebook-sync-"


def targets(portfolio: Path, only: str | None = None) -> list[str]:
    data = yaml.safe_load(portfolio.read_text(encoding="utf-8"))
    repos = [p["github_repo"] for p in data.get("projects", [])
             if p.get("governance_sync") is True and p.get("github_repo")]
    return [r for r in repos if not only or r == only]


def run(*cmd: str, cwd: Path | None = None, check: bool = True) -> str:
    res = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if check and res.returncode:
        raise SystemExit(f"{' '.join(cmd[:3])} failed: {res.stderr.strip()[:300]}")
    return res.stdout.strip()


def apply_sync(src: Path, dst: Path, sha: str) -> list[str]:
    """Copy synced files into a target checkout and re-vendor the rulebook; return notes."""
    notes: list[str] = []
    for rel in SYNC_FILES:
        (dst / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src / rel, dst / rel)
    run(sys.executable, "scripts/check-rulebook.py", "--update", sha, cwd=dst)
    template = dst / TEMPLATE_DST
    if not template.exists():
        template.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src / TEMPLATE_SRC, template)
    else:
        missing = [m for m in MARKERS if m not in template.read_text(encoding="utf-8")]
        if missing:
            notes.append(f"PR template lacks sections {missing}; update it by hand "
                         f"(model: {TEMPLATE_SRC}).")
    return notes


def sync_repo(repo: str, sha: str, dry: bool) -> str:
    with tempfile.TemporaryDirectory() as tmp:
        dst = Path(tmp) / "repo"
        run("gh", "repo", "clone", repo, str(dst), "--", "--depth", "1")
        base = run("git", "rev-parse", "--abbrev-ref", "HEAD", cwd=dst)
        branch = f"{BRANCH_PREFIX}{sha[:7]}"
        run("git", "checkout", "-q", "-b", branch, cwd=dst)
        notes = apply_sync(ROOT, dst, sha)
        if not run("git", "status", "--porcelain", cwd=dst):
            return f"{repo}: up to date"
        if dry:
            return f"{repo}: would open {branch} -> {base}\n" + run("git", "status", "--short", cwd=dst)
        run("git", "add", "-A", cwd=dst)
        run("git", "-c", "user.name=governance-sync", "-c", "user.email=noreply@github.com",
            "commit", "-q", "-m", f"governance: sync portfolio rulebook from portfolio-ops@{sha[:12]}",
            cwd=dst)
        run("git", "push", "-q", "origin", branch, cwd=dst)
        body = ("R0 sync of vendored governance files from "
                f"jerry200176-png/portfolio-ops@{sha}.\n\n## 參考做法\n- Copybara-style one-way sync; "
                "no local edits to vendored files.\n\n## 設計文件\n- portfolio-ops docs/governance-sync.md; "
                "重複檢查: byte copy only.\n\nRollback: revert this PR.\n"
                + "".join(f"\nNOTE: {n}" for n in notes))
        pr = json.loads(run("gh", "api", f"repos/{repo}/pulls", "-X", "POST", "-f",
                            f"title=governance: sync portfolio rulebook ({sha[:7]})", "-f",
                            f"head={branch}", "-f", f"base={base}", "-f", f"body={body}"))
        for old in json.loads(run("gh", "api", f"repos/{repo}/pulls?state=open&per_page=100")):
            if old["head"]["ref"].startswith(BRANCH_PREFIX) and old["number"] != pr["number"]:
                run("gh", "pr", "close", str(old["number"]), "-R", repo, "-c",
                    f"Superseded by #{pr['number']}", check=False)
        run("gh", "pr", "merge", str(pr["number"]), "-R", repo, "--auto", "--squash", check=False)
        return f"{repo}: opened {pr['html_url']}"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--sha", required=True)
    ap.add_argument("--portfolio", type=Path, default=ROOT / "portfolio.yaml")
    ap.add_argument("--only")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    if not re.fullmatch(r"[0-9a-f]{40}", args.sha):
        raise SystemExit("--sha must be a full 40-hex portfolio-ops commit")
    if not os.environ.get("GOVERNANCE_SYNC_TOKEN") and not os.environ.get("GH_TOKEN"):
        print("governance-sync: GOVERNANCE_SYNC_TOKEN not set; skipping (see docs/governance-sync.md)")
        return 0
    repos = targets(args.portfolio, args.only)
    print(f"governance-sync: {len(repos)} target(s): {', '.join(repos) or '-'}")
    failed = 0
    for repo in repos:
        try:
            print(sync_repo(repo, args.sha, args.dry_run))
        except SystemExit as exc:
            failed += 1
            print(f"{repo}: FAILED {exc}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
