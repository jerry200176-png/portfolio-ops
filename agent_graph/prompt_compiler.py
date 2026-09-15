"""Compile bounded node prompts for replaceable workers.

Prompt is execution input only — never canonical Run state.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from .durable_models import Attempt, Run
from .worker_contract import ALLOWED_OUTCOME_TYPES, RESULT_REL_PATH, RESULT_SCHEMA_VERSION


# Per-node scope: what the worker may do vs must not do.
NODE_SCOPE: dict[str, dict[str, Any]] = {
    "investigator": {
        "role": "investigator",
        "allowed_outcome_types": ["INVESTIGATION_COMPLETED", "NODE_FAILED"],
        "allowed_scope": [
            "Read repository files inside the bound worktree only",
            "Summarize findings needed for this node",
            f"Write a single structured result to {RESULT_REL_PATH}",
        ],
        "non_scope": [
            "Do not choose next_node or mutate graph/SQLite state",
            "Do not open PRs, merge, deploy, or touch production",
            "Do not modify other Runs or other workers' sessions",
            "Do not write outside the bound worktree",
        ],
        "success_condition": (
            "Produce a valid WorkerResult JSON with status=success and "
            "proposed_outcome.outcome_type=INVESTIGATION_COMPLETED (or NODE_FAILED)."
        ),
    },
    "builder": {
        "role": "builder",
        "allowed_outcome_types": ["BUILD_COMPLETED", "NODE_FAILED"],
        "allowed_scope": [
            "Make minimal code changes inside the bound worktree for this node",
            "Record head_sha of the worktree after changes",
            f"Write a single structured result to {RESULT_REL_PATH}",
        ],
        "non_scope": [
            "Do not choose next_node or mutate graph/SQLite state",
            "Do not open PRs, merge, deploy, or touch production",
            "Do not review or approve your own change as reviewer",
            "Do not write outside the bound worktree",
        ],
        "success_condition": (
            "Produce a valid WorkerResult JSON with status=success and "
            "proposed_outcome.outcome_type=BUILD_COMPLETED including head_sha."
        ),
    },
    "reviewer": {
        "role": "reviewer",
        "allowed_outcome_types": ["REVIEW_APPROVED", "REVIEW_REJECTED", "NODE_FAILED"],
        "allowed_scope": [
            "Review the bound worktree diff for the current head_sha",
            f"Write a single structured result to {RESULT_REL_PATH}",
        ],
        "non_scope": [
            "Do not choose next_node or mutate graph/SQLite state",
            "Do not merge, deploy, or rewrite history",
            "Do not approve as the same actor who built the change",
        ],
        "success_condition": (
            "Produce a valid WorkerResult JSON with REVIEW_APPROVED or REVIEW_REJECTED."
        ),
    },
    "human_gate": {
        "role": "human",
        "allowed_outcome_types": ["HUMAN_APPROVED", "HUMAN_REJECTED", "NODE_FAILED"],
        "allowed_scope": [
            "Record an explicit human gate decision for the current head_sha",
            f"Write a single structured result to {RESULT_REL_PATH}",
        ],
        "non_scope": [
            "Do not choose next_node or mutate graph/SQLite state",
            "Do not deploy or merge",
        ],
        "success_condition": (
            "Produce a valid WorkerResult JSON with HUMAN_APPROVED or HUMAN_REJECTED."
        ),
    },
}


RESULT_SCHEMA_HINT = {
    "schema_version": RESULT_SCHEMA_VERSION,
    "status": "success|failure|needs_human",
    "summary": "non-empty string",
    "idempotency_key": "<ATTEMPT_ID>:<OUTCOME_TYPE>",
    "artifacts": [{"kind": "string", "uri": "string"}],
    "evidence": [{"kind": "string", "ref": "string", "summary": "string"}],
    "proposed_outcome": {
        "outcome_type": sorted(ALLOWED_OUTCOME_TYPES),
        "actor_id": "string",
        "actor_role": "string",
        "head_sha": "40-char sha or null",
        "base_sha": "40-char sha or null",
        "conclusion": "string",
        "evidence": {"object": True},
        "repository": "owner/repo",
    },
    "forbidden_keys": ["next_node", "current_node", "run_status"],
}


@dataclass(frozen=True)
class CompiledPrompt:
    node: str
    text: str
    result_rel_path: str = RESULT_REL_PATH

    def to_dict(self) -> dict[str, Any]:
        return {
            "node": self.node,
            "result_rel_path": self.result_rel_path,
            "text": self.text,
        }


def compile_node_prompt(
    *,
    run: Run,
    attempt: Attempt,
    goal_objective: str,
    success_condition: Optional[str] = None,
    worktree: str,
    extra_instructions: Optional[str] = None,
) -> CompiledPrompt:
    """Build a bounded node prompt from canonical fields (not a DB dump)."""
    node = attempt.node
    if node not in NODE_SCOPE:
        raise ValueError(f"no prompt compiler scope for node={node}")
    scope = NODE_SCOPE[node]
    goal_success = success_condition or scope["success_condition"]
    lines = [
        "# Graph-managed worker task (bounded node)",
        "",
        "You are a replaceable Codex worker. Canonical Run state lives in SQLite;",
        "you must NOT edit the control-plane database or choose next_node.",
        "",
        "## Goal",
        goal_objective.strip(),
        "",
        "## Current node",
        f"- node: `{node}`",
        f"- role: `{scope['role']}`",
        f"- run_id: `{run.run_id}`",
        f"- attempt_id: `{attempt.attempt_id}`",
        f"- project: `{run.project}`",
        f"- expected_state_version: `{attempt.expected_state_version}`",
        f"- base_sha: `{run.base_sha}`",
        f"- head_sha: `{run.head_sha}`",
        "",
        "## Worktree (mandatory cwd)",
        f"`{worktree}`",
        "All reads/writes must stay inside this worktree.",
        "",
        "## Allowed scope",
        *[f"- {item}" for item in scope["allowed_scope"]],
        "",
        "## Non-scope (hard bans)",
        *[f"- {item}" for item in scope["non_scope"]],
        "",
        "## Success condition",
        goal_success,
        "",
        "## Allowed proposed_outcome.outcome_type values",
        ", ".join(f"`{t}`" for t in scope["allowed_outcome_types"]),
        "",
        "## Required result schema",
        "Write exactly one JSON file at:",
        f"`{worktree}/{RESULT_REL_PATH}`",
        "",
        "Shape (Phase 1A WorkerResult):",
        "```json",
        _json_pretty(RESULT_SCHEMA_HINT),
        "```",
        "",
        "Use idempotency_key = `{attempt_id}:{outcome_type}` with this attempt_id.",
        "actor_id must identify THIS worker process uniquely (e.g. include attempt_id).",
        "",
        "## Completion",
        "After writing a valid result.json, stop. Do not start other nodes.",
        "Do not resume or depend on any prior Codex conversation/thread.",
    ]
    if extra_instructions:
        lines.extend(["", "## Extra instructions", extra_instructions.strip()])
    return CompiledPrompt(node=node, text="\n".join(lines) + "\n")


def _json_pretty(payload: dict[str, Any]) -> str:
    import json

    return json.dumps(payload, indent=2, ensure_ascii=False)
