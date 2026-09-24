"""ExoProtocol-to-agent-control adapter. Exo remains an event producer only."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

from lifecycle_event import make_event


def _requested_status(args: list[str]) -> str:
    found: list[str] = []
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--set-status":
            if i + 1 >= len(args):
                raise ValueError("--set-status needs a value")
            found.append(args[i + 1])
            i += 2
        elif arg.startswith("--set-status="):
            found.append(arg.split("=", 1)[1])
            i += 1
        else:
            i += 1
    if len(found) != 1 or found[0] not in {"done", "keep", "review"}:
        raise ValueError("pass --set-status exactly once: done, keep, or review")
    return found[0]


def _verify_result(stdout: str, task_id: str, requested_status: str) -> bool:
    try:
        response = json.loads(stdout)
    except (TypeError, ValueError):
        return False
    if not isinstance(response, dict) or response.get("ok") is not True:
        return False
    result = response.get("data")
    return (isinstance(result, dict)
            and result.get("ticket_id") == task_id
            and result.get("set_status") == requested_status
            and result.get("ticket_status") == (None if requested_status == "keep" else requested_status))


def run_exo_finish(*, project: str, task_id: str, worktree: Path, args: list[str],
                   exo_command: str = "exo", agent_finish: Path,
                   cwd: Path | None = None, runner=subprocess.run) -> int:
    """Run Exo first; only then send a verified, canonical event to agent-control."""
    status = _requested_status(args)
    worktree = worktree.resolve()
    caller_cwd = (cwd or Path.cwd()).resolve()
    if caller_cwd == worktree or worktree in caller_cwd.parents:
        raise ValueError("run the adapter outside the worktree so its own process cannot block GC")
    if "--ticket-id" in args or any(arg.startswith("--ticket-id=") for arg in args):
        raise ValueError("ticket id is bound to task_id; do not override --ticket-id")
    if any(arg in {"--repo", "--format", "session-finish"} for arg in args):
        raise ValueError("pass session-finish options only; repo, format, and subcommand are adapter-owned")

    command = [exo_command, "--repo", str(worktree), "--format", "json",
               "session-finish", "--ticket-id", task_id, *args]
    try:
        result = runner(command, cwd=str(caller_cwd), capture_output=True, text=True, check=False)
    except KeyboardInterrupt:
        _emit(agent_finish, project, task_id,
              make_event(task_id, worktree, "aborted", "exo"), caller_cwd, runner)
        return 130
    except OSError as exc:
        print(f"Exo command could not start: {exc}", file=sys.stderr)
        _emit(agent_finish, project, task_id,
              make_event(task_id, worktree, "terminal_failed", "exo"), caller_cwd, runner)
        return 127

    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)

    if result.returncode != 0:
        state = "terminal_failed"
    elif not _verify_result(result.stdout, task_id, status):
        state = "terminal_failed"
        print("Exo exited successfully but its JSON result did not confirm the requested ticket state; GC not triggered.",
              file=sys.stderr)
    else:
        state = "terminal_success" if status == "done" else "idle"

    event = make_event(task_id, worktree, state, "exo")
    _emit(agent_finish, project, task_id, event, caller_cwd, runner)
    return result.returncode


def _emit(agent_finish: Path, project: str, task_id: str, event: dict[str, str],
          cwd: Path, runner) -> None:
    try:
        sent = runner([str(agent_finish), project, task_id, "--event-stdin"],
                      cwd=str(cwd), input=json.dumps(event), capture_output=True,
                      text=True, check=False)
        if sent.stdout:
            print(sent.stdout, end="")
        if sent.returncode:
            print(f"Lifecycle event was not accepted (exit {sent.returncode}); Exo finish state was left unchanged.",
                  file=sys.stderr)
    except (OSError, KeyboardInterrupt) as exc:
        print(f"Lifecycle event delivery failed ({exc}); Exo finish state was left unchanged.",
              file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True)
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--worktree", required=True, type=Path)
    parser.add_argument("--agent-finish", required=True, type=Path)
    parser.add_argument("--exo-command", default="exo")
    parser.add_argument("exo_args", nargs=argparse.REMAINDER,
                        help="explicit session-finish options after --")
    options = parser.parse_args(argv)
    args = options.exo_args
    if args and args[0] == "--":
        args = args[1:]
    try:
        return run_exo_finish(project=options.project, task_id=options.task_id,
                              worktree=options.worktree, args=args,
                              exo_command=options.exo_command,
                              agent_finish=options.agent_finish)
    except ValueError as exc:
        parser.error(str(exc))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
