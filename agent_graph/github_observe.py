"""Read-only GitHub observation adapters (Phase 1C).

Wraps `gh` CLI helpers. Never create/merge/close/comment/deploy.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from typing import Any, Optional, Protocol

from .observation import ObservableFact, _utcnow


class ObservationError(RuntimeError):
    """Read-only observation failed."""


class GitHubReader(Protocol):
    def pr_view(self, repo: str, pr_number: int) -> dict[str, Any]: ...

    def pr_checks(self, repo: str, pr_number: int) -> list[dict[str, Any]]: ...


@dataclass
class GhCliReader:
    """Thin wrapper around `gh pr view` / `gh pr checks` (read-only)."""

    gh_bin: str = "gh"
    timeout_sec: float = 60.0

    def _run(self, args: list[str]) -> str:
        # Hard deny mutation verbs even if caller misuses this class.
        forbidden = {
            "create",
            "merge",
            "close",
            "reopen",
            "comment",
            "edit",
            "ready",
            "review",
            "lock",
            "unlock",
            "delete",
        }
        for a in args:
            if a in forbidden:
                raise ObservationError(f"mutation verb refused: {a}")
        proc = subprocess.run(
            [self.gh_bin, *args],
            capture_output=True,
            text=True,
            timeout=self.timeout_sec,
            check=False,
        )
        if proc.returncode != 0:
            raise ObservationError(
                f"gh failed ({proc.returncode}): {(proc.stderr or proc.stdout).strip()}"
            )
        return proc.stdout

    def pr_view(self, repo: str, pr_number: int) -> dict[str, Any]:
        out = self._run(
            [
                "pr",
                "view",
                str(pr_number),
                "--repo",
                repo,
                "--json",
                "number,url,state,mergeable,mergedAt,headRefOid,statusCheckRollup,title",
            ]
        )
        return json.loads(out)

    def pr_checks(self, repo: str, pr_number: int) -> list[dict[str, Any]]:
        # Prefer rollup from pr view; checks command is secondary.
        view = self.pr_view(repo, pr_number)
        rollup = view.get("statusCheckRollup") or []
        if isinstance(rollup, list):
            return [c for c in rollup if isinstance(c, dict)]
        return []


@dataclass
class FakeGitHubReader:
    """Deterministic fixture reader for unit tests (no network)."""

    payload: dict[str, Any]

    def pr_view(self, repo: str, pr_number: int) -> dict[str, Any]:
        del repo
        data = dict(self.payload)
        data.setdefault("number", pr_number)
        return data

    def pr_checks(self, repo: str, pr_number: int) -> list[dict[str, Any]]:
        view = self.pr_view(repo, pr_number)
        rollup = view.get("statusCheckRollup") or []
        return [c for c in rollup if isinstance(c, dict)]


def _classify_ci(rollup: list[dict[str, Any]]) -> str:
    if not rollup:
        return "CI_PENDING"
    conclusions = []
    for item in rollup:
        status = str(item.get("status") or "").upper()
        conclusion = str(item.get("conclusion") or "").upper()
        if status and status not in ("COMPLETED", "SUCCESS"):
            if status in ("IN_PROGRESS", "QUEUED", "PENDING", "WAITING"):
                return "CI_PENDING"
        if conclusion in ("FAILURE", "TIMED_OUT", "CANCELLED", "ACTION_REQUIRED", "STARTUP_FAILURE"):
            return "CI_FAILED"
        if conclusion:
            conclusions.append(conclusion)
        elif status == "COMPLETED":
            conclusions.append("SUCCESS")
    if not conclusions:
        return "CI_PENDING"
    if all(c in ("SUCCESS", "NEUTRAL", "SKIPPED") for c in conclusions):
        return "CI_PASSED"
    if any(c == "FAILURE" for c in conclusions):
        return "CI_FAILED"
    return "CI_PENDING"


def observe_pull_request(
    *,
    repo: str,
    pr_number: int,
    reader: GitHubReader,
    source: str = "github",
    observed_at: Optional[str] = None,
) -> list[ObservableFact]:
    """Produce PR/CI facts bound to the observed head SHA. Read-only."""
    now = observed_at or _utcnow()
    view = reader.pr_view(repo, pr_number)
    head = str(view.get("headRefOid") or "")
    if not head:
        raise ObservationError(f"PR #{pr_number} missing headRefOid")
    external_ref = f"{repo}#pr/{pr_number}"
    evidence_ref = str(view.get("url") or external_ref)
    facts: list[ObservableFact] = [
        ObservableFact(
            fact_type="PR_EXISTS",
            source=source,
            external_ref=external_ref,
            observed_at=now,
            observed_head_sha=head,
            evidence_ref=evidence_ref,
            raw={"state": view.get("state"), "title": view.get("title")},
        ),
        ObservableFact(
            fact_type="PR_HEAD_OBSERVED",
            source=source,
            external_ref=external_ref,
            observed_at=now,
            observed_head_sha=head,
            evidence_ref=evidence_ref,
            raw={"headRefOid": head},
        ),
    ]
    mergeable = view.get("mergeable")
    if mergeable in ("MERGEABLE", True, "mergeable"):
        facts.append(
            ObservableFact(
                fact_type="PR_MERGEABLE",
                source=source,
                external_ref=external_ref,
                observed_at=now,
                observed_head_sha=head,
                evidence_ref=evidence_ref,
                raw={"mergeable": mergeable},
            )
        )
    if view.get("mergedAt") or str(view.get("state") or "").upper() == "MERGED":
        facts.append(
            ObservableFact(
                fact_type="PR_MERGED_EXTERNALLY",
                source=source,
                external_ref=external_ref,
                observed_at=now,
                observed_head_sha=head,
                evidence_ref=evidence_ref,
                raw={"mergedAt": view.get("mergedAt"), "state": view.get("state")},
            )
        )

    rollup = reader.pr_checks(repo, pr_number)
    ci_fact = _classify_ci(rollup)
    facts.append(
        ObservableFact(
            fact_type=ci_fact,
            source=source,
            external_ref=external_ref,
            observed_at=now,
            observed_head_sha=head,
            evidence_ref=evidence_ref,
            raw={"statusCheckRollup": rollup, "conclusion": ci_fact},
        )
    )
    return facts
