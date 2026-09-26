import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

LIB = Path(__file__).resolve().parents[1] / 'agent-control/lib'
sys.path.insert(0, str(LIB))
import artifact_maintenance as m


class MaintenanceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.tasks = self.root / 'tasks'
        self.wt = self.tasks / 'ticket'
        self.wt.mkdir(parents=True)
        self.sessions = self.root / 'sessions'
        self.sessions.mkdir()
        subprocess.run(['git', 'init', '-q', str(self.wt)], check=True)
        subprocess.run(['git', '-C', str(self.wt), 'config', 'user.email', 'test@example.test'], check=True)
        subprocess.run(['git', '-C', str(self.wt), 'config', 'user.name', 'test'], check=True)
        (self.wt / 'backend').mkdir()
        (self.wt / 'backend/composer.json').write_text('{}')
        (self.wt / 'backend/composer.lock').write_text('{}')
        (self.wt / '.gitignore').write_text('backend/vendor/\n.agent-session/\n')
        subprocess.run(['git', '-C', str(self.wt), 'add', '.'], check=True)
        subprocess.run(['git', '-C', str(self.wt), 'commit', '-qm', 'source'], check=True)
        self.target = self.wt / 'backend/vendor'
        self.target.mkdir()
        (self.target / 'package.php').write_text('<?php // pristine')
        self.pristine = self.root / 'rebuilt'
        self.pristine.mkdir()
        (self.pristine / 'package.php').write_text('<?php // pristine')
        manifest = dict(provenance_type='agent-session', project='alltrue', task_id='ticket',
                        session_id='session', worktree_path=str(self.wt), lifecycle_state='idle',
                        lifecycle_updated_at='2026-09-26T00:00:00Z')
        (self.wt / '.agent-session').mkdir()
        (self.wt / '.agent-session/manifest.json').write_text(json.dumps(manifest))
        self.registry = self.sessions / 'session.json'
        self.registry.write_text(json.dumps(manifest))
        evidence = self.root / 'evidence.txt'
        evidence.write_text('retained acceptance and pristine install log')
        record = dict(path=str(evidence), sha256=m.file_hash(evidence))
        self.plan = dict(worktree=str(self.wt), task_id='ticket', session_id='session',
                         target='backend/vendor', category='composer_vendor',
                         pristine=str(self.pristine), pristine_digest=m.digest(self.pristine),
                         source_tree=m.gc.run('git', '-C', str(self.wt), 'rev-parse', 'HEAD:backend').stdout.strip(),
                         source_files={p: m.file_hash(self.wt / p) for p in ['backend/composer.json', 'backend/composer.lock']},
                         rebuild_command='composer install --no-scripts', rebuild_evidence=[record], retained_evidence=[record])

    def verify(self, processes=None, complete=True):
        with patch.object(m, 'registered', return_value=[self.wt]):
            return m.verify(self.plan, self.root / 'bare', self.tasks, self.sessions,
                            processes or [], complete, [self.wt])

    def test_eligible_idle_never_updates_metadata(self):
        before = self.registry.read_bytes()
        self.assertEqual(self.verify(), self.target)
        self.assertEqual(before, self.registry.read_bytes())

    def test_incomplete_scan_and_process_block(self):
        with self.assertRaisesRegex(ValueError, 'process_scan_incomplete'):
            self.verify(complete=False)
        with self.assertRaisesRegex(ValueError, 'process_uses_worktree'):
            self.verify([dict(cwd=str(self.target))])

    def test_identity_and_active_state_block(self):
        row = json.loads(self.registry.read_text())
        row['task_id'] = 'other'
        self.registry.write_text(json.dumps(row))
        with self.assertRaisesRegex(ValueError, 'metadata_mismatch'):
            self.verify()
        row['task_id'] = 'ticket'
        row['lifecycle_state'] = 'active'
        row.pop('lifecycle_updated_at')
        self.registry.write_text(json.dumps(row))
        with self.assertRaisesRegex(ValueError, 'not_in_maintenance_state'):
            self.verify()

    def test_modified_package_and_lock_block(self):
        (self.target / 'package.php').write_text('unique modification')
        with self.assertRaisesRegex(ValueError, 'artifact_not_pristine'):
            self.verify()
        (self.wt / 'backend/composer.lock').write_text('different')
        with self.assertRaisesRegex(ValueError, 'source_modified'):
            self.verify()

    def test_storage_and_inplace_reference_block(self):
        self.plan['target'] = 'backend/storage'
        with self.assertRaisesRegex(ValueError, 'target_outside_scope'):
            self.verify()
        self.plan['target'] = 'backend/vendor'
        self.plan['pristine'] = str(self.target)
        with self.assertRaisesRegex(ValueError, 'pristine_not_isolated'):
            self.verify()

    def test_shared_symlink_and_hardlink_block(self):
        peer = self.tasks / 'peer'
        peer.mkdir()
        (peer / 'alias').symlink_to(self.target.parent, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'shared_reference'):
            m.references([self.wt, peer], self.target)
        os.link(self.target / 'package.php', self.root / 'shared.php')
        with self.assertRaisesRegex(ValueError, 'shared_inode'):
            m.digest(self.target)

    def test_evidence_loss_blocks(self):
        Path(self.plan['retained_evidence'][0]['path']).unlink()
        with self.assertRaisesRegex(ValueError, 'proof_file_not_regular'):
            self.verify()

    def test_symlink_inside_artifact_blocks(self):
        (self.target / 'alias').symlink_to(self.root / 'other')
        with self.assertRaisesRegex(ValueError, 'links_or_special_files'):
            m.digest(self.target)

    def test_apply_requires_receipt_and_rechecks_proof(self):
        plan = self.root / 'plan.json'
        plan.write_text(json.dumps(self.plan))
        receipt = self.root / 'receipt.json'
        args = ['maintenance', '--plan', str(plan), '--bare', str(self.root / 'bare'),
                '--task-root', str(self.tasks), '--session-dir', str(self.sessions),
                '--dry-run-receipt', str(receipt)]
        with patch.object(m, 'registered', return_value=[self.wt]), patch.object(m.gc, 'process_snapshot', return_value=([], True)):
            with patch.object(sys, 'argv', args + ['--apply']):
                self.assertEqual(m.main(), 1)
            self.assertTrue(self.target.exists())
            with patch.object(sys, 'argv', args):
                self.assertEqual(m.main(), 0)
            (self.target / 'package.php').write_text('changed after dryrun')
            with patch.object(sys, 'argv', args + ['--apply']):
                self.assertEqual(m.main(), 1)
            self.assertTrue(self.target.exists())
            (self.target / 'package.php').write_text('<?php // pristine')
            with patch.object(sys, 'argv', args + ['--apply']):
                self.assertEqual(m.main(), 0)
            self.assertFalse(self.target.exists())
            self.assertTrue((self.wt / 'backend/composer.lock').exists())
            self.assertTrue(self.pristine.exists())

    def package_plan(self, name="acme/package"):
        package = self.target / name
        package.mkdir(parents=True)
        (package / 'lib.php').write_text('reproducible package')
        pristine_package = self.pristine / name
        pristine_package.mkdir(parents=True)
        (pristine_package / 'lib.php').write_text('reproducible package')
        lock = self.wt / 'backend/composer.lock'
        lock.write_text(json.dumps(dict(packages=[dict(name=name)])))
        subprocess.run(['git', '-C', str(self.wt), 'add', 'backend/composer.lock'], check=True)
        subprocess.run(['git', '-C', str(self.wt), 'commit', '-qm', 'locked package'], check=True)
        self.plan['source_tree'] = m.gc.run('git', '-C', str(self.wt), 'rev-parse', 'HEAD:backend').stdout.strip()
        self.plan['source_files']['backend/composer.lock'] = m.file_hash(lock)
        self.plan['package_digests'] = {name: m.digest(pristine_package)}
        return package

    def test_locked_packages_allow_generated_metadata_difference(self):
        self.package_plan()
        (self.target / 'package.php').write_text('different generated metadata retained')
        self.assertEqual(self.verify(), self.target)

    def test_package_scope_rejects_unknown_traversal_and_modified_package(self):
        package = self.package_plan()
        expected = self.plan['package_digests']['acme/package']
        for name in ['../outside', 'composer/generated', 'unknown/package']:
            self.plan['package_digests'] = {name: expected}
            with self.assertRaisesRegex(ValueError, 'package_not_locked_or_unsafe'):
                self.verify()
        self.plan['package_digests'] = {'acme/package': expected}
        (package / 'lib.php').write_text('unique modification')
        with self.assertRaisesRegex(ValueError, 'package_not_pristine'):
            self.verify()

    def test_package_apply_retains_generated_and_unique_files(self):
        package = self.package_plan()
        generated = self.target / 'package.php'
        plan = self.root / 'plan.json'
        plan.write_text(json.dumps(self.plan))
        args = ['maintenance', '--plan', str(plan), '--bare', str(self.root / 'bare'),
                '--task-root', str(self.tasks), '--session-dir', str(self.sessions),
                '--dry-run-receipt', str(self.root / 'receipt.json')]
        with patch.object(m, 'registered', return_value=[self.wt]), patch.object(m.gc, 'process_snapshot', return_value=([], True)):
            with patch.object(sys, 'argv', args):
                self.assertEqual(m.main(), 0)
            with patch.object(sys, 'argv', args + ['--apply']):
                self.assertEqual(m.main(), 0)
        self.assertFalse(package.exists())
        self.assertTrue(generated.exists())
        self.assertTrue(self.target.exists())

    def test_unrelated_broken_symlink_does_not_block_target(self):
        peer = self.tasks / 'peer'
        peer.mkdir()
        (peer / 'broken').symlink_to(self.root / 'nonexistent')
        m.references([self.wt, peer], self.target)

    def test_target_alias_through_parent_blocks(self):
        peer = self.tasks / 'peer'
        peer.mkdir()
        (peer / 'alias').symlink_to(self.target.parent, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'shared_reference'):
            m.references([self.wt, peer], self.target)

    def test_package_parent_symlink_blocks(self):
        self.package_plan()
        namespace = self.target / 'acme'
        outside = self.root / 'outside-namespace'
        namespace.rename(outside)
        namespace.symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'package_alias'):
            self.verify()

    def test_partial_cleanup_reports_deleted_file_blocks(self):
        import contextlib
        import io
        package = self.package_plan()
        plan = self.root / 'plan.json'
        plan.write_text(json.dumps(self.plan))
        args = ['maintenance', '--plan', str(plan), '--bare', str(self.root / 'bare'),
                '--task-root', str(self.tasks), '--session-dir', str(self.sessions),
                '--dry-run-receipt', str(self.root / 'receipt.json')]
        def partial(path):
            (path / 'lib.php').unlink()
            raise OSError('simulated partial failure')
        with patch.object(m, 'registered', return_value=[self.wt]), patch.object(m.gc, 'process_snapshot', return_value=([], True)):
            with patch.object(sys, 'argv', args):
                self.assertEqual(m.main(), 0)
            output = io.StringIO()
            with patch.object(sys, 'argv', args + ['--apply']), patch.object(m.shutil, 'rmtree', side_effect=partial), contextlib.redirect_stdout(output):
                self.assertEqual(m.main(), 1)
            result = json.loads(output.getvalue())
            self.assertEqual(result['state'], 'skipped')
            self.assertGreater(result['deleted_bytes'], 0)
            self.assertTrue(package.exists())

    def activity_change_during_proof(self, change):
        plan = self.root / 'plan.json'
        plan.write_text(json.dumps(self.plan))
        args = ['maintenance', '--plan', str(plan), '--bare', str(self.root / 'bare'),
                '--task-root', str(self.tasks), '--session-dir', str(self.sessions),
                '--dry-run-receipt', str(self.root / 'receipt.json')]
        with patch.object(m, 'registered', return_value=[self.wt]), patch.object(m.gc, 'process_snapshot', return_value=([], True)):
            with patch.object(sys, 'argv', args):
                self.assertEqual(m.main(), 0)
        actual_digest = m.digest
        snapshots = [([], True)]
        def proof(path):
            result = actual_digest(path)
            change(snapshots)
            return result
        with patch.object(m, 'registered', return_value=[self.wt]), patch.object(m.gc, 'process_snapshot', side_effect=lambda: snapshots[-1]), patch.object(m, 'digest', side_effect=proof), patch.object(m.shutil, 'rmtree') as remove:
            with patch.object(sys, 'argv', args + ['--apply']):
                self.assertEqual(m.main(), 1)
            remove.assert_not_called()
        self.assertTrue(self.target.exists())

    def test_new_process_during_proof_prevents_removal(self):
        self.activity_change_during_proof(lambda snapshots: snapshots.append(
            ([dict(cwd=str(self.target), pid=999)], True)))

    def test_new_lease_during_proof_prevents_removal(self):
        def lease(_):
            row = json.loads(self.registry.read_text())
            row['lease_expires_at'] = '2999-01-01T00:00:00Z'
            self.registry.write_text(json.dumps(row))
        self.activity_change_during_proof(lease)

    def test_process_appears_during_final_proof_blocks_cheap_gate(self):
        plan = self.root / 'plan.json'
        plan.write_text(json.dumps(self.plan))
        args = ['maintenance', '--plan', str(plan), '--bare', str(self.root / 'bare'),
                '--task-root', str(self.tasks), '--session-dir', str(self.sessions),
                '--dry-run-receipt', str(self.root / 'receipt.json')]
        with patch.object(m, 'registered', return_value=[self.wt]), patch.object(m.gc, 'process_snapshot', return_value=([], True)):
            with patch.object(sys, 'argv', args):
                self.assertEqual(m.main(), 0)
        snapshots = [([], True), ([], True), ([dict(cwd=str(self.target), pid=999)], True)]
        with patch.object(m, 'registered', return_value=[self.wt]), patch.object(m.gc, 'process_snapshot', side_effect=snapshots), patch.object(m.shutil, 'rmtree') as remove:
            with patch.object(sys, 'argv', args + ['--apply']):
                self.assertEqual(m.main(), 1)
            remove.assert_not_called()

    def test_locked_composer_namespace_package_is_allowed(self):
        self.package_plan('composer/semver')
        self.assertEqual(self.verify(), self.target)
        for name in ['composer/installed.php', 'composer/autoload_static.php', 'composer']:
            self.plan['package_digests'] = {name: 'not-a-package'}
            with self.assertRaisesRegex(ValueError, 'package_not_locked_or_unsafe'):
                self.verify()

    def test_same_worktree_retained_bin_links_do_not_mean_cross_worktree_sharing(self):
        package = self.package_plan()
        bins = self.target / 'bin'
        bins.mkdir()
        (bins / 'tool').symlink_to(package / 'lib.php')
        (bins / 'unrelated').symlink_to(self.root / 'unrelated')
        self.assertEqual(self.verify(), self.target)
        self.assertTrue((bins / 'tool').is_symlink())

    def test_other_worktree_parent_alias_blocks_exact_package(self):
        package = self.package_plan()
        peer = self.tasks / 'peer'
        peer.mkdir()
        (peer / 'alias').symlink_to(self.target, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'shared_reference'):
            m.references([self.wt, peer], [package], owner=self.wt)

    def test_other_worktree_unrelated_vendor_metadata_link_does_not_block_packages(self):
        package = self.package_plan()
        peer = self.tasks / 'peer'
        peer.mkdir()
        (peer / 'metadata').symlink_to(self.target / 'package.php')
        m.references([self.wt, peer], [package], owner=self.wt)

    def test_peer_bare_shared_reference_blocks_primary_target(self):
        package = self.package_plan()
        peer = self.root / 'portfolio-task'
        peer.mkdir()
        (peer / 'shared').symlink_to(package)
        plan = self.root / 'plan.json'
        plan.write_text(json.dumps(self.plan))
        primary = self.root / 'alltrue.git'
        peer_bare = self.root / 'portfolio.git'
        args = ['maintenance', '--plan', str(plan), '--bare', str(primary),
                '--peer-bare', str(peer_bare), '--task-root', str(self.tasks),
                '--session-dir', str(self.sessions), '--dry-run-receipt', str(self.root / 'receipt.json')]
        with patch.object(m, 'registered', side_effect=lambda bare: [self.wt] if bare == primary else [peer]), patch.object(m.gc, 'process_snapshot', return_value=([], True)):
            with patch.object(sys, 'argv', args):
                self.assertEqual(m.main(), 1)
        self.assertTrue(package.exists())

    def test_peer_inventory_never_grants_target_eligibility(self):
        with patch.object(m, 'registered', return_value=[]):
            with self.assertRaisesRegex(ValueError, 'target_not_in_primary_alltrue_inventory'):
                m.verify(self.plan, self.root / 'bare', self.tasks, self.sessions, [], True, [self.wt])
