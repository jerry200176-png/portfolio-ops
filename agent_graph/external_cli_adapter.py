"""Provider-neutral external CLI worker adapter.

Launches a disposable independent process for one Attempt, then reads
``.agent-session/result.json``. Canonical Run/Attempt state stays in SQLite.

Domain ``worker_type`` is always ``external_cli``. Concrete runtimes
(Cursor Agent, Codex route, stub) are observational ``provider_id`` only —
never part of Goal/Run contracts.
"""

from __future__ import annotations

import json
import os
import signal
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional, Sequence

from .canonical_paths import (
    CanonicalPathError,
    assert_canonical_db_outside_worktree,
    safe_result_path,
)
from .durable_models import Attempt, Run
from .prompt_compiler import CompiledPrompt, compile_node_prompt
from .worker_contract import (
    CONTEXT_REL_PATH,
    RESULT_REL_PATH,
    WorkerResult,
    WorkerResultError,
    read_worker_result,
)

PROMPT_REL_PATH = ".agent-session/node-prompt.md"
LAUNCH_META_REL = ".agent-session/external-cli-launch.json"
INVOCATION_REL = ".agent-session/worker-invocation.json"

DEFAULT_CURSOR_AGENT = "/home/jerry/.local/bin/cursor-agent"
DEFAULT_STUB_WORKER = str(
    Path(__file__).resolve().parent.parent / "scripts" / "graph-external-cli-stub-worker.py"
)


CommandBuilder = Callable[[Path, str, dict[str, Any]], list[str]]


@dataclass
class ExternalCliLaunchMeta:
    """Observational launch metadata (not canonical state)."""

    command: list[str]
    provider_id: str
    role: str
    pid: Optional[int] = None
    exit_code: Optional[int] = None
    timed_out: bool = False
    stdout_path: Optional[str] = None
    stderr_path: Optional[str] = None
    result_path: Optional[str] = None
    prompt_path: Optional[str] = None
    invocation_path: Optional[str] = None
    worktree: Optional[str] = None
    failure_reason: Optional[str] = None
    extras: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "command": list(self.command),
            "provider_id": self.provider_id,
            "role": self.role,
            "pid": self.pid,
            "exit_code": self.exit_code,
            "timed_out": self.timed_out,
            "stdout_path": self.stdout_path,
            "stderr_path": self.stderr_path,
            "result_path": self.result_path,
            "prompt_path": self.prompt_path,
            "invocation_path": self.invocation_path,
            "worktree": self.worktree,
            "failure_reason": self.failure_reason,
            "extras": dict(self.extras),
        }


def build_stub_command(worktree: Path, prompt_text: str, ctx: dict[str, Any]) -> list[str]:
    stub = str(ctx.get("stub_bin") or DEFAULT_STUB_WORKER)
    return ["python3", stub, "--worktree", str(worktree)]


def build_cursor_agent_command(worktree: Path, prompt_text: str, ctx: dict[str, Any]) -> list[str]:
    binary = str(ctx.get("cursor_agent_bin") or os.environ.get("CURSOR_AGENT_BIN") or DEFAULT_CURSOR_AGENT)
    cmd = [
        binary,
        "--print",
        "--force",
        "--trust",
        "--workspace",
        str(worktree),
        "--output-format",
        "text",
    ]
    model = ctx.get("model") or os.environ.get("GRAPH_EXTERNAL_CLI_MODEL")
    if model:
        cmd.extend(["--model", str(model)])
    cmd.append(prompt_text)
    return cmd


def resolve_command_builder(provider_id: str) -> CommandBuilder:
    if provider_id in ("stub", "test_stub"):
        return build_stub_command
    if provider_id in ("cursor", "cursor_agent"):
        return build_cursor_agent_command
    raise WorkerResultError(f"unknown external_cli provider_id: {provider_id}")


class ExternalCliWorkerAdapter:
    """Spawn an independent CLI process; ingest structured WorkerResult."""

    worker_type = "external_cli"
    requires_execution_lease = True

    def __init__(
        self,
        *,
        provider_id: str = "stub",
        command_builder: Optional[CommandBuilder] = None,
        timeout_sec: float = 900.0,
        dry_run: bool = False,
        env: Optional[dict[str, str]] = None,
        terminate_grace_sec: float = 5.0,
        canonical_db_path: Optional[str | Path] = None,
        capabilities: Optional[Sequence[str]] = None,
        authorized_actions: Optional[Sequence[str]] = None,
        builder_context: Optional[dict[str, Any]] = None,
    ) -> None:
        self.provider_id = provider_id
        self.command_builder = command_builder or resolve_command_builder(provider_id)
        self.timeout_sec = float(timeout_sec)
        self.dry_run = dry_run
        self.env = env
        self.terminate_grace_sec = float(terminate_grace_sec)
        self.canonical_db_path = (
            Path(canonical_db_path).resolve() if canonical_db_path else None
        )
        self.capabilities = list(capabilities or ("coding_medium",))
        self.authorized_actions = list(authorized_actions or ("write_result", "edit_worktree"))
        self.builder_context = dict(builder_context or {})
        self.last_launch: Optional[ExternalCliLaunchMeta] = None
        self._active_proc: Optional[subprocess.Popen] = None

    def execute(
        self,
        *,
        run: Run,
        attempt: Attempt,
        context: dict[str, Any],
    ) -> WorkerResult:
        worktree = Path(context.get("WORKTREE") or run.worktree or ".").resolve()
        if not worktree.is_dir():
            raise WorkerResultError(f"worktree missing for external_cli worker: {worktree}")
        if worktree == Path("/home/jerry").resolve() or worktree == Path.home().resolve():
            raise WorkerResultError(
                "refusing to launch external_cli worker at home/root; require task worktree"
            )

        db_path = self.canonical_db_path or context.get("CANONICAL_DB_PATH")
        if db_path:
            try:
                assert_canonical_db_outside_worktree(db_path, worktree)
            except CanonicalPathError as exc:
                raise WorkerResultError(str(exc)) from exc

        goal_objective = str(context.get("GOAL_OBJECTIVE") or run.project)
        success_condition = context.get("SUCCESS_CONDITION")
        prompt = context.get("compiled_prompt")
        if isinstance(prompt, CompiledPrompt):
            compiled = prompt
        else:
            compiled = compile_node_prompt(
                run=run,
                attempt=attempt,
                goal_objective=goal_objective,
                success_condition=success_condition,
                worktree=str(worktree),
                extra_instructions=context.get("extra_instructions"),
            )

        session_dir = worktree / ".agent-session"
        session_dir.mkdir(parents=True, exist_ok=True)
        prompt_path = worktree / PROMPT_REL_PATH
        prompt_path.write_text(compiled.text, encoding="utf-8")
        try:
            result_path = safe_result_path(worktree)
        except CanonicalPathError as exc:
            raise WorkerResultError(str(exc)) from exc
        if result_path.exists() or result_path.is_symlink():
            result_path.unlink()

        role = str(context.get("role") or attempt.node or "implementation_worker")
        invocation = {
            "schema_version": "1.0",
            "role": role,
            "capabilities": list(self.capabilities),
            "work_ref": {
                "run_id": run.run_id,
                "attempt_id": attempt.attempt_id,
                "goal_id": run.goal_id,
                "node": attempt.node,
                "project": run.project,
            },
            "context_refs": {
                "prompt_path": PROMPT_REL_PATH,
                "context_path": CONTEXT_REL_PATH,
                "result_path": RESULT_REL_PATH,
                "base_sha": run.base_sha,
                "head_sha": run.head_sha,
                "goal_objective": goal_objective,
            },
            "authorized_actions": list(self.authorized_actions),
            "expected_result_schema": "agent_graph.worker_contract.WorkerResult/1.0",
            "execution_identity": {
                "run_id": run.run_id,
                "attempt_id": attempt.attempt_id,
                "expected_state_version": attempt.expected_state_version,
                "fencing_token": attempt.fencing_token,
                "worker_type": self.worker_type,
            },
            "provider_id": self.provider_id,
        }
        invocation_path = worktree / INVOCATION_REL
        invocation_path.write_text(
            json.dumps(invocation, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

        builder_ctx = dict(self.builder_context)
        builder_ctx.update({k: v for k, v in context.items() if isinstance(k, str)})
        cmd = self.command_builder(worktree, compiled.text, builder_ctx)

        stdout_path = session_dir / f"external-cli-{attempt.attempt_id}.stdout.log"
        stderr_path = session_dir / f"external-cli-{attempt.attempt_id}.stderr.log"
        meta = ExternalCliLaunchMeta(
            command=cmd,
            provider_id=self.provider_id,
            role=role,
            worktree=str(worktree),
            prompt_path=str(prompt_path),
            result_path=str(result_path),
            invocation_path=str(invocation_path),
            stdout_path=str(stdout_path),
            stderr_path=str(stderr_path),
        )
        self.last_launch = meta
        self._write_launch_meta(worktree, meta)

        if self.dry_run:
            meta.failure_reason = "dry_run"
            self._write_launch_meta(worktree, meta)
            return self._failure_result(attempt, "dry_run: external_cli not launched")

        env = self._merged_env()
        env.update(
            {
                "RUN_ID": run.run_id,
                "ATTEMPT_ID": attempt.attempt_id,
                "NODE": attempt.node,
                "PROJECT": run.project,
                "WORKTREE": str(worktree),
                "EXPECTED_STATE_VERSION": str(attempt.expected_state_version),
                "GRAPH_CONTROL_PLANE": "1",
                "GRAPH_WORKER_TYPE": self.worker_type,
                "GRAPH_PROVIDER_ID": self.provider_id,
                "WORKER_INVOCATION_PATH": str(invocation_path),
                "WORKER_RESULT_PATH": str(result_path),
            }
        )
        if attempt.fencing_token is not None:
            env["FENCING_TOKEN"] = str(attempt.fencing_token)

        proc: Optional[subprocess.Popen] = None
        try:
            with stdout_path.open("w", encoding="utf-8") as out_f, stderr_path.open(
                "w", encoding="utf-8"
            ) as err_f:
                proc = subprocess.Popen(
                    cmd,
                    cwd=str(worktree),
                    stdout=out_f,
                    stderr=err_f,
                    env=env,
                    start_new_session=True,
                    text=True,
                )
                self._active_proc = proc
                meta.pid = proc.pid
                self._write_launch_meta(worktree, meta)
                timed_out = False
                try:
                    exit_code = proc.wait(timeout=self.timeout_sec)
                except subprocess.TimeoutExpired:
                    timed_out = True
                    self._reap_process_group(proc.pid)
                    exit_code = proc.poll()
                    if exit_code is None:
                        try:
                            exit_code = proc.wait(timeout=self.terminate_grace_sec)
                        except subprocess.TimeoutExpired:
                            self._kill_process_group(proc.pid)
                            exit_code = proc.wait(timeout=self.terminate_grace_sec)
        except Exception as exc:
            if proc is not None and proc.poll() is None and proc.pid:
                self._reap_process_group(proc.pid)
            meta.failure_reason = f"adapter_exception:{exc}"
            self._write_launch_meta(worktree, meta)
            raise
        finally:
            self._active_proc = None

        meta.exit_code = exit_code
        meta.timed_out = timed_out
        self.last_launch = meta
        self._write_launch_meta(worktree, meta)

        if timed_out:
            meta.failure_reason = "timeout"
            self._write_launch_meta(worktree, meta)
            return self._failure_result(
                attempt, f"external_cli timed out after {self.timeout_sec}s", key_suffix="TIMEOUT"
            )
        if exit_code != 0 and not result_path.is_file():
            meta.failure_reason = f"nonzero_exit:{exit_code}"
            self._write_launch_meta(worktree, meta)
            return self._failure_result(
                attempt,
                f"external_cli exited {exit_code} without result.json",
                key_suffix=f"EXIT_{exit_code}",
            )
        if not result_path.is_file():
            meta.failure_reason = "missing_result"
            self._write_launch_meta(worktree, meta)
            return self._failure_result(
                attempt,
                "external_cli exited without writing .agent-session/result.json",
                key_suffix="MISSING_RESULT",
            )
        try:
            result_path = safe_result_path(worktree)
            return read_worker_result(result_path)
        except (WorkerResultError, CanonicalPathError) as exc:
            meta.failure_reason = f"malformed_result:{exc}"
            self._write_launch_meta(worktree, meta)
            return self._failure_result(
                attempt, f"malformed result.json: {exc}", key_suffix="MALFORMED_RESULT"
            )

    def _merged_env(self) -> dict[str, str]:
        env = dict(os.environ)
        if self.env:
            env.update(self.env)
        return env

    @staticmethod
    def _terminate_process_group(pid: int) -> None:
        try:
            os.killpg(pid, signal.SIGTERM)
        except ProcessLookupError:
            return

    @staticmethod
    def _kill_process_group(pid: int) -> None:
        try:
            os.killpg(pid, signal.SIGKILL)
        except ProcessLookupError:
            return

    def _reap_process_group(self, pid: int) -> None:
        self._terminate_process_group(pid)
        deadline = time.time() + self.terminate_grace_sec
        while time.time() < deadline:
            try:
                os.killpg(pid, 0)
            except ProcessLookupError:
                return
            time.sleep(0.05)
        self._kill_process_group(pid)

    def _write_launch_meta(self, worktree: Path, meta: ExternalCliLaunchMeta) -> None:
        path = worktree / LAUNCH_META_REL
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(meta.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")

    @staticmethod
    def _failure_result(
        attempt: Attempt,
        summary: str,
        *,
        key_suffix: str = "FAILURE",
        blocker: Optional[str] = None,
    ) -> WorkerResult:
        evidence = {"kind": "adapter", "ref": attempt.attempt_id, "summary": summary}
        if blocker:
            evidence["blocker"] = blocker
        return WorkerResult(
            status="failure",
            summary=summary,
            idempotency_key=f"{attempt.attempt_id}:{key_suffix}",
            artifacts=(),
            evidence=(evidence,),
            proposed_outcome=None,
        )
