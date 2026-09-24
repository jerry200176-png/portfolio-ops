#!/usr/bin/env python3
"""Conservative, worktree-local cleanup for proven regenerable artifacts."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import tempfile

DEFAULT_CONFIG = Path(__file__).resolve().parents[1] / "config" / "artifact-gc.json"
LOCKFILES = ("package-lock.json", "npm-shrinkwrap.json", "pnpm-lock.yaml", "yarn.lock", "bun.lock", "bun.lockb")


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, text=True, capture_output=True, check=False)


def load_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError):
        return {}


def under(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return path.resolve() != root.resolve()
    except (OSError, ValueError):
        return False


def process_snapshot(proc_root: Path = Path("/proc")) -> tuple[list[dict], bool]:
    rows, complete = [], True
    try:
        pids = [p for p in proc_root.iterdir() if p.name.isdigit()]
    except OSError:
        return rows, False
    for proc in pids:
        try:
            if proc.stat().st_uid != os.getuid():
                continue
            if (proc / "stat").read_text().split(") ", 1)[1].startswith("Z "):
                continue
            cwd = Path(os.readlink(proc / "cwd"))
            env = (proc / "environ").read_bytes().split(b"\0")
            session = next((v.split(b"=", 1)[1].decode(errors="replace") for v in env
                            if v.startswith(b"AGENT_SESSION_ID=")), "")
            rows.append({"pid": int(proc.name), "cwd": cwd, "session_id": session})
        except FileNotFoundError:
            continue
        except PermissionError:
            try:
                comm = (proc / "comm").read_text().strip()
            except OSError:
                comm = ""
            # The non-dumpable user-session supervisor has no task CWD; its
            # agents are separate same-user processes and are inspected above.
            if comm not in {"systemd", "(sd-pam)"}:
                complete = False
        except (OSError, IndexError, ValueError):
            continue
    return rows, complete


def package_context(parent: Path, repo: Path) -> tuple[Path, dict] | None:
    """Find a lock-backed package root; workspace roots must declare the path."""
    cursor, repo = parent.resolve(), repo.resolve()
    while cursor == repo or under(cursor, repo):
        manifest = cursor / "package.json"
        if manifest.is_file() and any((cursor / name).is_file() for name in LOCKFILES):
            data = load_json(manifest)
            if cursor == parent.resolve():
                return cursor, data
            rel = parent.resolve().relative_to(cursor).as_posix()
            workspaces = data.get("workspaces", [])
            if isinstance(workspaces, dict):
                workspaces = workspaces.get("packages", [])
            if isinstance(workspaces, list) and any(
                Path(rel).match(str(pattern).rstrip("/") + "/**") or Path(rel).match(str(pattern))
                for pattern in workspaces
            ):
                return cursor, data
        if cursor == repo:
            break
        cursor = cursor.parent
    return None


def proven(target: Path, repo: Path, proof: str) -> bool:
    context = package_context(target.parent, repo)
    if not context:
        return False
    _, package = context
    if proof == "locked_package":
        return True
    deps = {**package.get("dependencies", {}), **package.get("devDependencies", {})}
    return (proof == "next_build" and "next" in deps
            and "next build" in str(package.get("scripts", {}).get("build", "")))


def artifact_paths(repo: Path, targets: list[dict]) -> list[tuple[Path, str]]:
    names = {str(row.get("name")): str(row.get("proof")) for row in targets}
    found = []
    for root, dirs, _ in os.walk(repo, followlinks=False):
        dirs[:] = [d for d in dirs if d != ".git"]
        for name in list(dirs):
            if name in names:
                found.append((Path(root) / name, names[name]))
                dirs.remove(name)
    return found


def allocated_size(path: Path) -> int:
    total = 0
    if path.is_symlink():
        return total
    for root, dirs, files in os.walk(path, followlinks=False):
        dirs[:] = [d for d in dirs if not (Path(root) / d).is_symlink()]
        for name in files:
            try:
                info = (Path(root) / name).lstat()
                if stat.S_ISREG(info.st_mode):
                    total += getattr(info, "st_blocks", 0) * 512 or info.st_size
            except OSError:
                continue
    return total


def artifact_safety(repo: Path, path: Path, proof: str) -> str:
    if path.is_symlink():
        return "symlink"
    rel = path.resolve().relative_to(repo.resolve()).as_posix()
    tracked = run("git", "-C", str(repo), "ls-files", "--", rel)
    if tracked.returncode or tracked.stdout.strip():
        return "tracked_content"
    ignored = run("git", "-C", str(repo), "check-ignore", "--no-index", "-q", "--", rel)
    if ignored.returncode:
        return "not_git_ignored"
    if not proven(path, repo, proof):
        return "regeneration_not_proven"
    return ""


def session_rows(worktree: Path, session_dir: Path) -> tuple[list[tuple[Path, dict]], str]:
    rows = []
    try:
        for file in session_dir.glob("*.json"):
            data = load_json(file)
            if data.get("worktree_path") and Path(data["worktree_path"]).resolve() == worktree.resolve():
                state = data.get("lifecycle_state")
                if state is not None and state not in {"active", "idle", "terminal"}:
                    return [], "session_lifecycle_invalid"
                if state in {"idle", "terminal"} and not data.get("lifecycle_updated_at"):
                    return [], "session_lifecycle_timestamp_missing"
                if state == "active" and data.get("lifecycle_updated_at"):
                    return [], "session_lifecycle_timestamp_invalid"
                rows.append((file, data))
    except OSError:
        return [], "session_inventory_unavailable"
    if rows and any(not row.get("session_id") for _, row in rows):
        return [], "session_manifest_missing_id"
    return rows, "" if rows else "no_session_manifest"


def active_lease(worktree: Path, rows: list[tuple[Path, dict]], now: dt.datetime) -> str:
    for _, data in rows:
        expiry = data.get("lease_expires_at")
        if expiry:
            try:
                if dt.datetime.fromisoformat(str(expiry).replace("Z", "+00:00")) > now:
                    return "session_lease_active"
            except ValueError:
                return "session_lease_unknown"
    for lock in (worktree / ".agent-session" / "lease.json",
                 worktree / ".exo" / "locks" / "ticket.lock.json"):
        if not lock.exists():
            continue
        data = load_json(lock)
        if not data:
            return "lease_state_unknown"
        state = str(data.get("status", "")).lower()
        expiry = data.get("lease_expires_at") or data.get("expires_at")
        if expiry:
            try:
                if dt.datetime.fromisoformat(str(expiry).replace("Z", "+00:00")) > now:
                    return "active_lease"
            except ValueError:
                return "lease_state_unknown"
        elif state in {"active", "held"}:
            return "active_lease"
    return ""


def update_state(rows: list[tuple[Path, dict]], state: str, dry_run: bool) -> None:
    stamp = dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")
    for path, data in rows:
        if data.get("lifecycle_state") != state:
            data["lifecycle_state"], data["lifecycle_updated_at"] = state, stamp
        if not dry_run:
            if path.is_symlink():
                raise OSError(f"refusing symlink session manifest: {path}")
            mode = path.stat().st_mode & 0o777
            with tempfile.NamedTemporaryFile("w", dir=path.parent, delete=False, encoding="utf-8") as stream:
                temp = Path(stream.name)
                stream.write(json.dumps(data, indent=2) + "\n")
            os.chmod(temp, mode)
            os.replace(temp, path)


def evaluate(worktree: Path, session_dir: Path, policy: dict, allowed_roots: list[Path],
             processes: list[dict], process_scan_ok: bool, *, terminal_signal: bool = False,
             lifecycle_state: str = "terminal", dry_run: bool = True,
             now: dt.datetime | None = None) -> dict:
    worktree = worktree.resolve()
    if not any(under(worktree, root) for root in allowed_roots) or not (worktree / ".git").exists():
        return {"path": str(worktree), "state": "unsafe", "reason": "outside_registered_roots"}
    repo = Path(run("git", "-C", str(worktree), "rev-parse", "--show-toplevel").stdout.strip())
    if not repo.is_dir():
        return {"path": str(worktree), "state": "unsafe", "reason": "git_root_unknown"}
    found = artifact_paths(repo, policy.get("targets", []))
    observed = [{"path": str(path), "bytes": allocated_size(path), "kind": path.name} for path, _ in found]
    if not process_scan_ok:
        return {"path": str(worktree), "state": "active", "reason": "process_scan_incomplete",
                "observed_artifacts": observed}
    for process in processes:
        cwd = Path(process.get("cwd", "/")).resolve()
        if under(cwd, worktree) or cwd == worktree:
            return {"path": str(worktree), "state": "active", "reason": "process_uses_worktree",
                    "pid": process.get("pid"), "observed_artifacts": observed}
    rows, error = session_rows(worktree, session_dir)
    ids = {str(row.get("session_id")) for _, row in rows if row.get("session_id")}
    if any(process.get("session_id") in ids for process in processes):
        return {"path": str(worktree), "state": "active", "reason": "session_process_active",
                "observed_artifacts": observed}
    now = now or dt.datetime.now(dt.timezone.utc)
    lease = active_lease(worktree, rows, now)
    if lease:
        state = "unsafe" if "unknown" in lease else "active"
        return {"path": str(worktree), "state": state, "reason": lease, "observed_artifacts": observed}
    if error:
        return {"path": str(worktree), "state": "unknown", "reason": error,
                "observed_artifacts": observed}
    quarantine = any("quarantine" in root.parts and under(worktree, root) for root in allowed_roots)
    if terminal_signal:
        update_state(rows, lifecycle_state, dry_run)
    states = {row.get("lifecycle_state") for _, row in rows}
    if not states or not states.issubset({"terminal", "idle"}):
        return {"path": str(worktree), "state": "active" if "active" in states else "unknown",
                "reason": "not_confirmed_terminal", "observed_artifacts": observed}
    if quarantine:
        metadata = rows[0][1].get("quarantine", {})
        if not isinstance(metadata, dict) or any(not metadata.get(k) for k in
                                                 ("owner", "task", "reason", "entered_at", "state")):
            return {"path": str(worktree), "state": "unsafe", "reason": "quarantine_metadata_incomplete",
                    "observed_artifacts": observed}
        if metadata.get("state") != "terminal" or metadata.get("task") != rows[0][1].get("task_id"):
            return {"path": str(worktree), "state": "unsafe", "reason": "quarantine_not_terminal_or_task_mismatch",
                    "observed_artifacts": observed}
    candidates, skipped = [], []
    for path, proof in found:
        reason = artifact_safety(repo, path, proof)
        if reason:
            skipped.append({"path": str(path), "reason": reason})
        else:
            candidates.append({"path": str(path), "bytes": allocated_size(path), "kind": path.name})
    if terminal_signal and not dry_run:
        latest, complete = process_snapshot()
        if not complete or any(under(Path(p.get("cwd", "/")).resolve(), worktree)
                               or Path(p.get("cwd", "/")).resolve() == worktree
                               or p.get("session_id") in ids for p in latest):
            return {"path": str(worktree), "state": "active", "reason": "process_started_during_gc",
                    "observed_artifacts": observed}
        for item in candidates:
            target = Path(item["path"])
            proof = next(t["proof"] for t in policy["targets"] if t["name"] == target.name)
            if artifact_safety(repo, target, proof):
                return {"path": str(worktree), "state": "unsafe", "reason": "artifact_changed_during_gc",
                        "observed_artifacts": observed}
            shutil.rmtree(target)
    return {"path": str(worktree), "state": "eligible", "reason": "terminal_and_safe",
            "artifacts": candidates, "observed_artifacts": observed, "skipped_artifacts": skipped}


def gib(value: int) -> str:
    return f"{value / (1024 ** 3):.2f} GiB"


def pressure(policy: dict, free_bytes: int | None) -> str:
    if free_bytes is None:
        return "UNKNOWN"
    limits = policy["capacity_gib"]
    if free_bytes < float(limits["critical_below"]) * 1024**3:
        return "CRITICAL"
    if free_bytes < float(limits["pressure_below"]) * 1024**3:
        return "PRESSURE"
    return "NORMAL"


def workspace_scan(projects: list[tuple[str, Path, Path, Path]], session_dir: Path,
                   policy: dict) -> list[dict]:
    processes, complete = process_snapshot()
    rows = []
    for _, bare, task_root, quarantine_root in projects:
        listing = run("git", "-C", str(bare), "worktree", "list", "--porcelain")
        if listing.returncode:
            rows.append({"path": str(bare), "state": "unsafe", "reason": "worktree_list_failed"})
            continue
        for block in listing.stdout.split("\n\n"):
            path = next((line[9:] for line in block.splitlines() if line.startswith("worktree ")), "")
            worktree = Path(path).resolve() if path else None
            if worktree and str(worktree) != str(bare.resolve()) and any(under(worktree, r) for r in
                                                                          (task_root, quarantine_root)):
                rows.append(evaluate(worktree, session_dir, policy, [task_root, quarantine_root],
                                     processes, complete))
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("finish", "workspace"))
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--session-dir", type=Path, required=True)
    parser.add_argument("--worktree", type=Path)
    parser.add_argument("--bare", type=Path)
    parser.add_argument("--task-root", type=Path)
    parser.add_argument("--quarantine-root", type=Path)
    parser.add_argument("--project", nargs=4, action="append", metavar=("NAME", "BARE", "TASK_ROOT", "QUARANTINE_ROOT"))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--idle", action="store_true", help="mark an ended CLI session idle instead of task-terminal")
    args = parser.parse_args(argv)
    policy = load_json(args.config)
    if not policy.get("targets") or not policy.get("capacity_gib"):
        parser.error("artifact policy is missing or invalid")
    if args.mode == "finish":
        if not all((args.worktree, args.bare, args.task_root, args.quarantine_root)):
            parser.error("finish needs --worktree, --bare, --task-root and --quarantine-root")
        listing = run("git", "-C", str(args.bare), "worktree", "list", "--porcelain")
        registered = {Path(line[9:]).resolve() for line in listing.stdout.splitlines()
                      if line.startswith("worktree ")}
        if listing.returncode or args.worktree.resolve() not in registered:
            print(json.dumps({"state": "unsafe", "reason": "not_registered_worktree"}))
            return 0
        processes, complete = process_snapshot()
        row = evaluate(args.worktree, args.session_dir, policy,
                       [args.task_root, args.quarantine_root], processes, complete,
                       terminal_signal=True, lifecycle_state="idle" if args.idle else "terminal",
                       dry_run=args.dry_run)
        print(json.dumps(row, ensure_ascii=False))
        return 0
    projects = [(name, Path(bare), Path(tasks), Path(quarantine))
                for name, bare, tasks, quarantine in (args.project or [])]
    rows = workspace_scan(projects, args.session_dir, policy)
    eligible = [a for row in rows for a in row.get("artifacts", [])]
    observed = [a for row in rows for a in row.get("observed_artifacts", [])]
    root_free = shutil.disk_usage("/").free
    try:
        c_free = shutil.disk_usage("/mnt/c").free
    except OSError:
        c_free = None
    level = pressure(policy, c_free)
    if level == "CRITICAL":
        rows.sort(key=lambda r: -sum(a["bytes"] for a in r.get("artifacts", [])))
    counts = {s: sum(r["state"] == s for r in rows) for s in ("eligible", "active", "unknown", "unsafe")}
    print(f"Capacity: {level}; C free={gib(c_free) if c_free is not None else 'UNKNOWN'}; Linux / free={gib(root_free)}")
    print(f"Recognized artifact usage (all states): {gib(sum(a['bytes'] for a in observed))}")
    print(f"Eligible worktrees: {counts['eligible']}")
    print(f"Would reclaim: {gib(sum(a['bytes'] for a in eligible))}")
    print(f"Skipped active: {counts['active']}")
    print(f"Skipped unsafe/unknown: {counts['unsafe'] + counts['unknown']}")
    for row in rows:
        print(json.dumps(row, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
