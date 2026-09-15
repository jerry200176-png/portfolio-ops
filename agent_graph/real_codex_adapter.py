"""Real Codex CLI worker adapter (replaceable, non-durable).

Uses existing ``codex-route`` → ``codex exec`` gateway. Does not own worktrees;
bind via agent-start / worktree helpers. Canonical state remains SQLite.
"""

from __future__ import annotations

import json
import os
import signal
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional, Sequence

from .canonical_paths import (
    CanonicalPathError,
    assert_canonical_db_outside_worktree,
    safe_result_path,
)
from .durable_models import Attempt, Run
from .prompt_compiler import CompiledPrompt, compile_node_prompt
from .worker_contract import WorkerResult, WorkerResultError, read_worker_result


DEFAULT_CODEX_ROUTE = "/home/jerry/.local/bin/codex-route"
PROMPT_REL_PATH = ".agent-session/node-prompt.md"
LAUNCH_META_REL = ".agent-session/codex-launch.json"


def _read_usage_limit_detail(*log_paths: Path) -> Optional[str]:
    """Return a single-line detail if Codex hit account usage limit."""
    chunks: list[str] = []
    for path in log_paths:
        try:
            chunks.append(Path(path).read_text(encoding="utf-8", errors="replace"))
        except OSError:
            continue
    blob = "\n".join(chunks)
    if "usage limit" not in blob.lower():
        return None
    for line in blob.splitlines():
        if "usage limit" in line.lower():
            return line.strip()
    return "codex_usage_limit"


@dataclass
class CodexLaunchMeta:
    """Observational metadata for one Attempt execution (not canonical state)."""

    command: list[str]
    pid: Optional[int] = None
    exit_code: Optional[int] = None
    timed_out: bool = False
    stdout_path: Optional[str] = None
    stderr_path: Optional[str] = None
    result_path: Optional[str] = None
    prompt_path: Optional[str] = None
    worktree: Optional[str] = None
    route_plan: dict[str, Any] = field(default_factory=dict)
    failure_reason: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "command": list(self.command),
            "pid": self.pid,
            "exit_code": self.exit_code,
            "timed_out": self.timed_out,
            "stdout_path": self.stdout_path,
            "stderr_path": self.stderr_path,
            "result_path": self.result_path,
            "prompt_path": self.prompt_path,
            "worktree": self.worktree,
            "route_plan": dict(self.route_plan),
            "failure_reason": self.failure_reason,
        }


class RealCodexWorkerAdapter:
    """Launch a real Codex CLI process for one Attempt, then read result.json."""

    worker_type = "codex"

    def __init__(
        self,
        *,
        codex_route: str = DEFAULT_CODEX_ROUTE,
        timeout_sec: float = 900.0,
        sandbox: str = "workspace-write",
        ephemeral: bool = True,
        complexity: str = "low",
        ambiguity: str = "low",
        blast_radius: str = "low",
        risk: str = "low",
        workload: str = "coding",
        dry_run: bool = False,
        extra_codex_args: Optional[Sequence[str]] = None,
        env: Optional[dict[str, str]] = None,
        terminate_grace_sec: float = 5.0,
        canonical_db_path: Optional[str | Path] = None,
    ) -> None:
        self.codex_route = codex_route
        self.timeout_sec = float(timeout_sec)
        self.sandbox = sandbox
        self.ephemeral = ephemeral
        self.complexity = complexity
        self.ambiguity = ambiguity
        self.blast_radius = blast_radius
        self.risk = risk
        self.workload = workload
        self.dry_run = dry_run
        self.extra_codex_args = list(extra_codex_args or ())
        self.env = env
        self.terminate_grace_sec = float(terminate_grace_sec)
        self.canonical_db_path = (
            Path(canonical_db_path).resolve() if canonical_db_path else None
        )
        self.last_launch: Optional[CodexLaunchMeta] = None
        self._active_proc: Optional[subprocess.Popen] = None

    def build_route_command(
        self,
        *,
        worktree: Path,
        prompt_text: str,
        dry_run: Optional[bool] = None,
    ) -> list[str]:
        """Construct argv for ``codex-route`` → ``codex exec`` (testable)."""
        use_dry = self.dry_run if dry_run is None else dry_run
        cmd: list[str] = [
            self.codex_route,
            "--complexity",
            self.complexity,
            "--ambiguity",
            self.ambiguity,
            "--blast-radius",
            self.blast_radius,
            "--risk",
            self.risk,
            "--workload",
            self.workload,
        ]
        if use_dry:
            cmd.append("--dry-run")
        cmd.append("--")
        # Fresh process identity: never resume/fork prior threads.
        cmd.extend(["-C", str(worktree), "-s", self.sandbox])
        if self.ephemeral:
            cmd.append("--ephemeral")
        cmd.extend(self.extra_codex_args)
        cmd.append(prompt_text)
        return cmd

    def build_codex_exec_preview(
        self,
        *,
        worktree: Path,
        prompt_text: str,
    ) -> tuple[list[str], dict[str, Any]]:
        """Resolve route plan (dry-run) and return planned ``codex exec`` argv."""
        route_cmd = self.build_route_command(
            worktree=worktree, prompt_text=prompt_text, dry_run=True
        )
        proc = subprocess.run(
            route_cmd, capture_output=True, text=True, check=False, env=self._merged_env()
        )
        if proc.returncode != 0:
            raise WorkerResultError(
                f"codex-route dry-run failed ({proc.returncode}): {proc.stderr.strip()}"
            )
        plan = json.loads(proc.stdout)
        # Recreate the exec argv with the same profile the route selected.
        exec_cmd = ["codex", "exec", "--profile", plan["profile"]]
        if plan.get("reasoning_effort_override"):
            exec_cmd += [
                "-c",
                f'model_reasoning_effort="{plan["reasoning_effort_override"]}"',
            ]
        exec_cmd.extend(["-C", str(worktree), "-s", self.sandbox])
        if self.ephemeral:
            exec_cmd.append("--ephemeral")
        exec_cmd.extend(self.extra_codex_args)
        exec_cmd.append(prompt_text)
        return exec_cmd, plan

    def execute(
        self,
        *,
        run: Run,
        attempt: Attempt,
        context: dict[str, Any],
    ) -> WorkerResult:
        worktree = Path(context.get("WORKTREE") or run.worktree or ".").resolve()
        if not worktree.is_dir():
            raise WorkerResultError(f"worktree missing for Codex worker: {worktree}")
        if worktree == Path("/home/jerry").resolve() or worktree == Path.home().resolve():
            raise WorkerResultError(
                "refusing to launch Codex worker at home/root; require task worktree"
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
        # Clear prior attempt result so missing-result failures are deterministic.
        if result_path.exists() or result_path.is_symlink():
            result_path.unlink()

        stdout_path = session_dir / f"codex-{attempt.attempt_id}.stdout.log"
        stderr_path = session_dir / f"codex-{attempt.attempt_id}.stderr.log"

        route_cmd = self.build_route_command(
            worktree=worktree, prompt_text=compiled.text, dry_run=False
        )
        # Capture planned exec for evidence even when we invoke via route.
        try:
            exec_preview, plan = self.build_codex_exec_preview(
                worktree=worktree, prompt_text=compiled.text
            )
        except WorkerResultError as exc:
            meta = CodexLaunchMeta(
                command=route_cmd,
                worktree=str(worktree),
                prompt_path=str(prompt_path),
                result_path=str(result_path),
                failure_reason=str(exc),
            )
            self.last_launch = meta
            self._write_launch_meta(worktree, meta)
            return self._failure_result(attempt, f"codex-route planning failed: {exc}")

        meta = CodexLaunchMeta(
            command=route_cmd,
            worktree=str(worktree),
            prompt_path=str(prompt_path),
            result_path=str(result_path),
            stdout_path=str(stdout_path),
            stderr_path=str(stderr_path),
            route_plan=plan,
        )
        meta.route_plan["exec_preview"] = exec_preview
        self.last_launch = meta

        if self.dry_run:
            meta.failure_reason = "dry_run"
            self._write_launch_meta(worktree, meta)
            return self._failure_result(attempt, "dry_run: Codex not launched")

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
            }
        )

        proc: Optional[subprocess.Popen] = None
        try:
            with stdout_path.open("w", encoding="utf-8") as out_f, stderr_path.open(
                "w", encoding="utf-8"
            ) as err_f:
                # New session so timeout signals only hit this worker tree.
                proc = subprocess.Popen(
                    route_cmd,
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
                attempt, f"Codex timed out after {self.timeout_sec}s", key_suffix="TIMEOUT"
            )
        usage_detail = _read_usage_limit_detail(stdout_path, stderr_path)
        if usage_detail:
            meta.failure_reason = "codex_usage_limit"
            self._write_launch_meta(worktree, meta)
            return self._failure_result(
                attempt,
                f"codex_usage_limit: {usage_detail}",
                key_suffix="USAGE_LIMIT",
                blocker="codex_usage_limit",
            )
        if exit_code != 0:
            meta.failure_reason = f"nonzero_exit:{exit_code}"
            self._write_launch_meta(worktree, meta)
            # Still try to ingest a well-formed result if present; otherwise fail.
            if not result_path.is_file():
                return self._failure_result(
                    attempt,
                    f"Codex exited {exit_code} without result.json",
                    key_suffix=f"EXIT_{exit_code}",
                )

        if not result_path.is_file():
            meta.failure_reason = "missing_result"
            self._write_launch_meta(worktree, meta)
            return self._failure_result(
                attempt,
                "Codex exited without writing .agent-session/result.json",
                key_suffix="MISSING_RESULT",
            )

        try:
            # Re-validate path immediately before read (symlink race).
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
            pass

    @staticmethod
    def _kill_process_group(pid: int) -> None:
        try:
            os.killpg(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass

    def _reap_process_group(self, pid: int) -> None:
        """TERM then KILL only this adapter's process group; never other workers."""
        self._terminate_process_group(pid)
        deadline = time.time() + self.terminate_grace_sec
        while time.time() < deadline:
            try:
                os.killpg(pid, 0)
            except ProcessLookupError:
                return
            time.sleep(0.05)
        self._kill_process_group(pid)

    @staticmethod
    def _write_launch_meta(worktree: Path, meta: CodexLaunchMeta) -> None:
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
        evidence: dict[str, Any] = {
            "kind": "worker_failure",
            "ref": attempt.attempt_id,
            "summary": summary,
        }
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


def wait_pid_exited(pid: int, *, timeout_sec: float = 30.0) -> bool:
    """Return True if pid is not running within timeout (observational)."""
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return True
        except PermissionError:
            # Process exists but not owned — treat as still running.
            time.sleep(0.1)
            continue
        time.sleep(0.1)
    try:
        os.kill(pid, 0)
        return False
    except ProcessLookupError:
        return True
