#!/usr/bin/env python3
"""Exact, externally rebuilt artifacts only; never changes lifecycle metadata."""
import argparse
from contextlib import ExitStack
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat

import artifact_gc as gc

TARGETS = {
    'composer_vendor': {'backend/vendor'},
    'build_output': {'frontend/dist_build'},
    'tool_cache': {'frontend/node_modules/.vite', 'frontend/node_modules/.vite-temp'},
}


def digest(path):
    """Content/type/mode digest; reject links, special files and shared inodes."""
    if path.is_symlink() or not path.is_dir():
        raise ValueError('target_not_regular_directory')
    result = hashlib.sha256()
    def failure(error):
        raise error
    for root, dirs, files in os.walk(path, followlinks=False, onerror=failure):
        dirs.sort()
        for name in sorted(dirs + files):
            item = Path(root) / name
            info = item.lstat()
            if not (stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode)):
                raise ValueError('links_or_special_files')
            if stat.S_ISREG(info.st_mode) and info.st_nlink != 1:
                raise ValueError('shared_inode')
            result.update(json.dumps([item.relative_to(path).as_posix(),
                                      stat.S_IMODE(info.st_mode), stat.S_ISDIR(info.st_mode),
                                      info.st_size if stat.S_ISREG(info.st_mode) else None]).encode())
            if item.is_file():
                with item.open('rb') as stream:
                    for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                        result.update(chunk)
    return result.hexdigest()


def file_hash(path):
    if path.is_symlink() or not path.is_file():
        raise ValueError('proof_file_not_regular')
    return hashlib.sha256(path.read_bytes()).hexdigest()


def registered(bare):
    listing = gc.run('git', '-C', str(bare), 'worktree', 'list', '--porcelain')
    if listing.returncode:
        raise ValueError('worktree_inventory_failed')
    return sorted({Path(line[9:]).resolve() for line in listing.stdout.splitlines()
                   if line.startswith('worktree ') and Path(line[9:]).resolve() != bare.resolve()})


def references(worktrees, targets, owner=None):
    """Never follow directory links; reject aliases into target or its parents."""
    targets = [targets] if isinstance(targets, Path) else targets
    def failure(error):
        raise error
    for worktree in worktrees:
        if owner is not None and worktree == owner:
            continue
        for root, dirs, files in os.walk(worktree, followlinks=False, onerror=failure):
            dirs[:] = [name for name in dirs if name != '.git']
            for name in dirs + files:
                path = Path(root) / name
                if path.is_symlink():
                    dest = path.resolve(strict=False)
                    if any(dest == target or gc.under(dest, target) or gc.under(target, dest)
                           for target in targets):
                        raise ValueError('shared_reference:' + str(path))


def activity_gate(plan, task_root, sessions, processes, complete, worktrees):
    wt = Path(plan['worktree']).resolve()
    if not complete:
        raise ValueError('process_scan_incomplete')
    if wt not in worktrees or not gc.under(wt, task_root):
        raise ValueError('not_registered_managed_worktree')
    manifest = gc.current_session_manifest(wt)
    rows, error = gc.session_rows(wt, sessions)
    if error or not manifest or manifest['project'] != 'alltrue':
        raise ValueError(error or 'current_session_unmanaged')
    for _, row in rows:
        for key in ('task_id', 'session_id', 'project', 'worktree_path'):
            if row.get(key) != manifest.get(key):
                raise ValueError('session_metadata_mismatch')
        if row.get('lifecycle_state') not in {'idle', 'terminal'}:
            raise ValueError('not_in_maintenance_state')
    if any(plan.get(key) != manifest.get(key) for key in ('task_id', 'session_id')):
        raise ValueError('plan_identity_mismatch')
    lease = gc.active_lease(wt, rows, dt.datetime.now(dt.timezone.utc))
    if lease:
        raise ValueError(lease)
    for proc in processes:
        paths = [Path(proc.get('cwd', '/'))] + [Path(p) for p in proc.get('open_paths', [])]
        if proc.get('session_id') == manifest['session_id'] or any(
                p.resolve() == wt or gc.under(p, wt) for p in paths):
            raise ValueError('process_uses_worktree')
    return wt


def verify(plan, bare, task_root, sessions, processes, complete, worktrees):
    wt = activity_gate(plan, task_root, sessions, processes, complete, worktrees)
    rel = plan['target']
    if rel not in TARGETS.get(plan['category'], set()):
        raise ValueError('target_outside_scope')
    target = wt / rel
    if target.resolve() != target or target.is_symlink():
        raise ValueError('target_alias')
    tracked = gc.run('git', '-C', str(wt), 'ls-files', '--', rel)
    if tracked.returncode or tracked.stdout.strip():
        raise ValueError('tracked_content')
    if gc.run('git', '-C', str(wt), 'check-ignore', '--no-index', '-q', '--', rel).returncode:
        raise ValueError('not_git_ignored')
    scope = 'backend' if plan['category'] == 'composer_vendor' else 'frontend'
    tree = gc.run('git', '-C', str(wt), 'rev-parse', 'HEAD:' + scope)
    if tree.returncode or tree.stdout.strip() != plan['source_tree']:
        raise ValueError('source_tree_changed')
    for revision in ('', '--cached'):
        args = ['git', '-C', str(wt), 'diff', '--quiet'] + ([revision] if revision else []) + ['--', scope]
        if gc.run(*args).returncode:
            raise ValueError('source_modified')
    required = ['backend/composer.json', 'backend/composer.lock'] if scope == 'backend' else ['frontend/package.json']
    if scope == 'frontend':
        locks = [scope + '/' + name for name in gc.LOCKFILES if (wt / scope / name).is_file()]
        if not locks:
            raise ValueError('lock_missing')
        required += locks
    for relfile in required:
        if gc.run('git', '-C', str(wt), 'ls-files', '--error-unmatch', relfile).returncode:
            raise ValueError('source_not_tracked')
        if plan['source_files'].get(relfile) != file_hash(wt / relfile):
            raise ValueError('lock_or_manifest_changed')
    pristine = Path(plan['pristine']).absolute()
    if pristine.resolve() != pristine or pristine == target or any(
            pristine == root or gc.under(pristine, root) for root in worktrees + [task_root]):
        raise ValueError('pristine_not_isolated')
    if not plan.get('rebuild_command') or not plan.get('rebuild_evidence') or not plan.get('retained_evidence'):
        raise ValueError('rebuild_or_retained_evidence_missing')
    for record in plan['rebuild_evidence'] + plan['retained_evidence']:
        path = Path(record['path']).absolute()
        if path.resolve() != path or path == target or gc.under(path, target):
            raise ValueError('evidence_inside_target_or_alias')
        if file_hash(path) != record['sha256']:
            raise ValueError('evidence_changed')
    packages = plan.get('package_digests')
    if packages is not None:
        if plan['category'] != 'composer_vendor' or not isinstance(packages, dict) or not packages:
            raise ValueError('invalid_package_scope')
        lock = gc.load_json(wt / 'backend/composer.lock')
        locked = {package.get('name') for package in lock.get('packages', []) + lock.get('packages-dev', [])}
        for name, expected in packages.items():
            # Locked two-segment Composer packages only. Keep generated
            # vendor/composer, bins, installed manifests and unknown files.
            parts = name.split('/')
            if (name not in locked or len(parts) != 2 or any(part in {'', '.', '..', 'bin'} for part in parts)
                    or any(not all(c.isalnum() or c in '-_.' for c in part) for part in parts)):
                raise ValueError('package_not_locked_or_unsafe')
            if (target / name).resolve() != target / name or (pristine / name).resolve() != pristine / name:
                raise ValueError('package_alias:' + name)
            if digest(pristine / name) != expected or digest(target / name) != expected:
                raise ValueError('package_not_pristine:' + name)
    else:
        expected = plan['pristine_digest']
        if digest(pristine) != expected or digest(target) != expected:
            raise ValueError('artifact_not_pristine')
    exact_targets = [target / name for name in packages] if packages is not None else [target]
    references(worktrees, exact_targets, owner=wt)
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--bare', type=Path, required=True)
    parser.add_argument('--task-root', type=Path, required=True)
    parser.add_argument('--session-dir', type=Path, required=True)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--dry-run-receipt', type=Path, required=True)
    args = parser.parse_args()
    raw = args.plan.read_bytes()
    plan_hash = hashlib.sha256(raw).hexdigest()
    plan = json.loads(raw)
    result = {'plan_sha256': plan_hash, 'worktree': plan.get('worktree'), 'target': plan.get('target'), 'deleted_bytes': 0}
    try:
        worktrees = registered(args.bare)
        with ExitStack() as stack:
            # Same locks used by canonical agent-start; this does not control
            # ungoverned external writers. Any observed use fails closed.
            for wt in worktrees:
                stack.enter_context(gc.lifecycle_lock(wt, args.session_dir))
            if registered(args.bare) != worktrees:
                raise ValueError('worktree_inventory_changed')
            processes, complete = gc.process_snapshot()
            target = verify(plan, args.bare, args.task_root, args.session_dir, processes, complete, worktrees)
            targets = [target / name for name in plan['package_digests']] if 'package_digests' in plan else [target]
            result.update(state='eligible', bytes=sum(gc.allocated_size(path) for path in targets),
                          exact_targets=[str(path) for path in targets])
            if args.apply:
                if args.dry_run_receipt.is_symlink():
                    raise ValueError('receipt_alias')
                receipt = gc.load_json(args.dry_run_receipt)
                if receipt.get('state') != 'eligible' or receipt.get('plan_sha256') != plan_hash:
                    raise ValueError('matching_dry_run_required')
                # Full revalidation uses a new process snapshot, not the earlier
                # observation preceding potentially expensive proof hashing.
                fresh_processes, fresh_complete = gc.process_snapshot()
                verify(plan, args.bare, args.task_root, args.session_dir,
                       fresh_processes, fresh_complete, worktrees)
                if registered(args.bare) != worktrees:
                    raise ValueError('worktree_inventory_changed')
                # The final cheap gate follows all hashing/reference work.
                # Repeat for each exact package: no ongoing worker may be
                # missed because it appeared during earlier package removal.
                for path in targets:
                    final_processes, final_complete = gc.process_snapshot()
                    activity_gate(plan, args.task_root, args.session_dir,
                                  final_processes, final_complete, worktrees)
                    if path.resolve() != path or path.is_symlink():
                        raise ValueError('artifact_alias_before_removal')
                    shutil.rmtree(path)
                result.update(state='deleted', deleted_bytes=result['bytes'])
            else:
                if args.dry_run_receipt.exists():
                    raise ValueError('receipt_already_exists')
                args.dry_run_receipt.parent.mkdir(parents=True, exist_ok=True)
                with args.dry_run_receipt.open('x') as stream:
                    json.dump(result, stream, indent=2)
    except (OSError, ValueError, KeyError, TypeError, RuntimeError) as exc:
        if args.apply and 'targets' in locals() and 'bytes' in result:
            result['deleted_bytes'] = result['bytes'] - sum(gc.allocated_size(path) for path in targets if path.exists())
        result.update(state='skipped', reason=str(exc))
    print(json.dumps(result))
    return 0 if result['state'] in {'eligible', 'deleted'} else 1


if __name__ == '__main__':
    raise SystemExit(main())
