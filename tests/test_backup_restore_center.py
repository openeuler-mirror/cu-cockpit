import json
import os
import sqlite3
import tempfile
import unittest
import warnings
import zipfile
from contextlib import closing
from pathlib import Path
from unittest.mock import Mock, patch

from osmanager.system_management.backup_center import (
    backup_lock, backup_sqlite, create_backup_archive, import_backup_archive,
    initialize_installation, read_backup_index, validate_backup_archive, verify_sqlite,
    write_backup_index,
)
from osmanager.system_management.backup_restore import (
    confirm_restore, preflight_restore, restore_confirmed,
)


class SqliteBackupTest(unittest.TestCase):
    def test_backup_copies_large_live_database(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'source.sqlite3'
            destination = Path(directory) / 'snapshot.sqlite3'
            with closing(sqlite3.connect(source)) as database:
                database.execute('CREATE TABLE data (value BLOB)')
                database.execute('INSERT INTO data VALUES (zeroblob(1200000))')
                database.commit()
                backup_sqlite(source, destination)
            with closing(sqlite3.connect(destination)) as snapshot:
                self.assertEqual(snapshot.execute('SELECT length(value) FROM data').fetchone()[0], 1200000)

    def test_damaged_sqlite_returns_false(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory).resolve() / 'damaged.sqlite3'
            path.write_bytes(b'not a SQLite database')
            self.assertFalse(verify_sqlite(path))


class BackupIdentityTest(unittest.TestCase):
    def test_same_version_reuses_installation_key(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            identity = initialize_installation(root, '1.0')
            self.assertEqual(initialize_installation(root, '1.0'), identity)
            self.assertEqual(len(identity['hmac_key']), 64)

    def test_explicit_version_update_preserves_identity_and_rejects_old_archive(self):
        from osmanager.system_management.backup_center import (
            read_installation, update_installation_version,
        )

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            identity = initialize_installation(root, '1.0')
            database = root / 'source.sqlite3'
            with closing(sqlite3.connect(database)) as connection:
                connection.execute('CREATE TABLE data (value INTEGER)')
                connection.commit()
            record = create_backup_archive(root, database, {}, '1.0', 'creator')
            with backup_lock(root):
                updated = update_installation_version(root, '1.0', '2.0')
            self.assertEqual(updated, {**identity, 'application_version': '2.0'})
            self.assertEqual(read_installation(root, '2.0'), updated)
            self.assertEqual((root / 'metadata.json').stat().st_mode & 0o777, 0o600)
            with self.assertRaisesRegex(ValueError, 'another application version'):
                read_installation(root, '1.0')
            with self.assertRaisesRegex(ValueError, 'different format or installation'):
                validate_backup_archive(root, root / f'{record["archive_id"]}.zip', '2.0')


class BackupIndexTest(unittest.TestCase):
    def test_private_index_atomic_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            self.assertEqual(root.stat().st_mode & 0o777, 0o700)
            initial = {'tasks': {}, 'backups': {}}
            updated = {'tasks': {'task-1': {}}, 'backups': {}}
            write_backup_index(root, initial)
            self.assertEqual(read_backup_index(root), initial)
            write_backup_index(root, updated)
            self.assertEqual(read_backup_index(root), updated)
            self.assertFalse(any(path.name.startswith('.index-') for path in root.iterdir()))

    def test_locked_index_rejects_second_write_without_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            initial = {'tasks': {}, 'backups': {}}
            updated = {'tasks': {'task-1': {}}, 'backups': {}}
            write_backup_index(root, initial)
            with backup_lock(root):
                with self.assertRaises(BlockingIOError):
                    write_backup_index(root, updated)
                self.assertEqual(read_backup_index(root), initial)
            self.assertEqual(read_backup_index(root), initial)


class BackupArchiveTest(unittest.TestCase):
    def test_create_archive_under_existing_backup_lock(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            initialize_installation(root, '1.0')
            database = root / 'source.sqlite3'
            with closing(sqlite3.connect(database)) as connection:
                connection.execute('CREATE TABLE data (value INTEGER)')
                connection.commit()
            with backup_lock(root):
                record = create_backup_archive(root, database, {}, '1.0', 'creator', locked=True)
            archive = root / f'{record["archive_id"]}.zip'
            self.assertEqual(validate_backup_archive(root, archive, '1.0')['archive_id'],
                             record['archive_id'])
            self.assertEqual(read_backup_index(root)['backups'][record['archive_id']], record)

    def test_invalid_zip_directory_rejected_before_zipfile_construction(self):
        import struct

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            initialize_installation(root, '1.0')
            archive = root / 'candidate.zip'
            with zipfile.ZipFile(archive, 'w') as package:
                package.writestr('manifest.json', '{}')
                package.writestr('app.sqlite3', b'SQLite format 3\x00')
            original = archive.read_bytes()
            eocd = original.rfind(b'PK\x05\x06')
            for label, offset, format_code, value in (
                    ('directory bytes', 12, '<I', 16385),
                    ('member count', 10, '<H', 65535)):
                with self.subTest(label=label):
                    damaged = bytearray(original)
                    struct.pack_into(format_code, damaged, eocd + offset, value)
                    archive.write_bytes(damaged)
                    with patch('osmanager.system_management.backup_center.zipfile.ZipFile',
                               side_effect=AssertionError('ZipFile constructed')):
                        with self.assertRaisesRegex(ValueError, 'invalid ZIP directory'):
                            validate_backup_archive(root, archive, '1.0')

    def test_index_directory_sync_failure_preserves_published_archive(self):
        import os
        import stat

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            initialize_installation(root, '1.0')
            database = root / 'source.sqlite3'
            with closing(sqlite3.connect(database)) as connection:
                connection.execute('CREATE TABLE data (value INTEGER)')
                connection.commit()
            original_fsync = os.fsync
            failed = False

            def fail_directory_sync(descriptor):
                nonlocal failed
                if stat.S_ISDIR(os.fstat(descriptor).st_mode) and not failed:
                    failed = True
                    raise OSError('directory sync failed')
                return original_fsync(descriptor)

            with patch('osmanager.system_management.backup_center.os.fsync',
                       side_effect=fail_directory_sync):
                with self.assertRaisesRegex(OSError, 'directory sync failed'):
                    create_backup_archive(root, database, {}, '1.0', 'creator')
            self.assertTrue(failed)
            published = read_backup_index(root)['backups']
            self.assertEqual(len(published), 1)
            archive_id = next(iter(published))
            self.assertEqual(validate_backup_archive(
                root, root / f'{archive_id}.zip', '1.0')['archive_id'], archive_id)
            retry = create_backup_archive(root, database, {}, '1.0', 'creator')
            self.assertIn(retry['archive_id'], read_backup_index(root)['backups'])

    def test_signed_archive_contains_sqlite_and_config(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            initialize_installation(root, '1.0')
            database = root / 'source.sqlite3'
            with closing(sqlite3.connect(database)) as connection:
                connection.execute('CREATE TABLE data (value TEXT)')
                connection.execute('INSERT INTO data VALUES (?)', ('saved',))
                connection.commit()
            config = root / 'service.conf'
            config.write_bytes(b'enabled=true\n')
            record = create_backup_archive(root, database, {'service': config}, '1.0', 'creator')
            archive = root / f'{record["archive_id"]}.zip'
            manifest = validate_backup_archive(root, archive, '1.0')
            self.assertEqual(set(manifest['members']), {'app.sqlite3', 'configs/service.bin'})
            self.assertEqual(manifest['archive_id'], record['archive_id'])
            with zipfile.ZipFile(archive) as package:
                self.assertEqual(package.read('configs/service.bin'), b'enabled=true\n')
                self.assertEqual(package.read('app.sqlite3')[:16], b'SQLite format 3\x00')

    def test_import_same_installation_archive(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory).resolve()
            source, target = base / 'source', base / 'target'
            source.mkdir(mode=0o700)
            target.mkdir(mode=0o700)
            initialize_installation(source, '1.0')
            identity = target / 'metadata.json'
            identity.write_bytes((source / 'metadata.json').read_bytes())
            identity.chmod(0o600)
            database = source / 'source.sqlite3'
            with closing(sqlite3.connect(database)) as connection:
                connection.execute('CREATE TABLE data (value INTEGER)')
                connection.commit()
            record = create_backup_archive(source, database, {}, '1.0', 'creator')
            archive = source / f'{record["archive_id"]}.zip'
            with archive.open('rb') as uploaded:
                imported = import_backup_archive(target, uploaded, '1.0', 'importer')
            self.assertEqual(imported['actor'], 'importer')
            self.assertEqual(imported, read_backup_index(target)['backups'][record['archive_id']])
            self.assertEqual((target / archive.name).read_bytes(), archive.read_bytes())
            self.assertFalse(any(path.name.startswith('.import-') for path in target.iterdir()))

    def test_import_rejects_tampered_signature_and_member(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            initialize_installation(root, '1.0')
            database = root / 'source.sqlite3'
            with closing(sqlite3.connect(database)) as connection:
                connection.execute('CREATE TABLE data (value INTEGER)')
                connection.commit()
            config = root / 'service.conf'
            config.write_bytes(b'original')
            record = create_backup_archive(root, database, {'service': config}, '1.0', 'creator')
            archive = root / f'{record["archive_id"]}.zip'
            for alteration in ('signature', 'member'):
                with self.subTest(alteration=alteration):
                    damaged = root / 'tampered.zip'
                    with zipfile.ZipFile(archive) as original, zipfile.ZipFile(
                            damaged, 'w') as modified:
                        for name in original.namelist():
                            payload = original.read(name)
                            if alteration == 'signature' and name == 'manifest.json':
                                manifest = json.loads(payload)
                                manifest['signature'] = ('0' if manifest['signature'][0] != '0'
                                                         else '1') * 64
                                payload = json.dumps(manifest).encode()
                            if alteration == 'member' and name == 'configs/service.bin':
                                payload = b'altered!'
                            modified.writestr(name, payload)
                    with damaged.open('rb') as uploaded:
                        with self.assertRaises(ValueError):
                            import_backup_archive(root, uploaded, '1.0', 'importer')
                    self.assertEqual(set(read_backup_index(root)['backups']), {record['archive_id']})
                    damaged.unlink()

    def test_import_rejects_traversal_and_duplicate_zip_members(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            initialize_installation(root, '1.0')
            archive = root / 'candidate.zip'
            for extra in ('../escape', 'app.sqlite3'):
                with self.subTest(extra=extra):
                    with warnings.catch_warnings(record=True), zipfile.ZipFile(
                            archive, 'w') as package:
                        package.writestr('manifest.json', '{}')
                        package.writestr('app.sqlite3', b'not SQLite')
                        package.writestr(extra, b'payload')
                    with archive.open('rb') as uploaded:
                        with self.assertRaises(ValueError):
                            import_backup_archive(root, uploaded, '1.0', 'importer')
                    self.assertFalse((root / 'index.json').exists())
                    self.assertFalse((root.parent / 'escape').exists())
                    archive.unlink()

    def test_import_rejects_other_installation_and_version(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory).resolve()
            source, target = base / 'source', base / 'target'
            source.mkdir(mode=0o700)
            target.mkdir(mode=0o700)
            initialize_installation(source, '1.0')
            initialize_installation(target, '1.0')
            database = source / 'source.sqlite3'
            with closing(sqlite3.connect(database)) as connection:
                connection.execute('CREATE TABLE data (value INTEGER)')
                connection.commit()
            record = create_backup_archive(source, database, {}, '1.0', 'creator')
            archive = source / f'{record["archive_id"]}.zip'
            cases = ((target, '1.0', 'different format or installation'),
                     (source, '2.0', 'another application version'))
            for root, version, message in cases:
                with self.subTest(version=version, root=root):
                    with archive.open('rb') as uploaded:
                        with self.assertRaisesRegex(ValueError, message):
                            import_backup_archive(root, uploaded, version, 'importer')
                    self.assertFalse((target / 'index.json').exists())
                    self.assertEqual(set(read_backup_index(source)['backups']), {record['archive_id']})

    def test_import_rejects_excessive_expanded_size(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            initialize_installation(root, '1.0')
            archive = root / 'candidate.zip'
            with zipfile.ZipFile(archive, 'w') as package:
                package.writestr('manifest.json', '{}')
                package.writestr('app.sqlite3', b'SQLite format 3\x00')
            with patch('osmanager.system_management.backup_center.MAX_EXPANDED_BYTES', 17):
                with archive.open('rb') as uploaded:
                    with self.assertRaisesRegex(ValueError, 'expanded size limit'):
                        import_backup_archive(root, uploaded, '1.0', 'importer')
            self.assertFalse((root / 'index.json').exists())
            self.assertFalse(any(path.name.startswith('.import-') for path in root.iterdir()))


class RestoreConfirmedTest(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name).resolve()
        initialize_installation(self.root, '1.0')
        self.database = self.root / 'app.sqlite3'
        with closing(sqlite3.connect(self.database)) as connection:
            connection.execute('CREATE TABLE data (value TEXT)')
            connection.execute('INSERT INTO data VALUES (?)', ('old',))
            connection.commit()
        self.config = self.root / 'service.conf'
        self.config.write_bytes(b'old config')
        self.archive = create_backup_archive(
            self.root, self.database, {'service': self.config}, '1.0', 'tester')
        with closing(sqlite3.connect(self.database)) as connection:
            connection.execute('UPDATE data SET value = ?', ('new',))
            connection.commit()
        self.config.write_bytes(b'new config')
        environment = patch.dict(os.environ, {'BACKUP_RESTORE_SERVICES': 'cu-cockpit.service'})
        environment.start()
        self.addCleanup(environment.stop)
        self.controller = Mock()
        self.controller.is_active.side_effect = [True, False, True]

    def _confirmed_task(self):
        preview = preflight_restore(self.root, self.archive['archive_id'], self.database,
                                    {'service': self.config}, '1.0', 'tester',
                                    ['cu-cockpit.service'])
        confirm_restore(self.root, preview['task_id'], preview['token'], 'tester')
        return preview['task_id']

    def _write_uncheckpointed_wal(self, value):
        connection = sqlite3.connect(self.database)
        self.addCleanup(connection.close)
        connection.execute('PRAGMA journal_mode=WAL')
        connection.execute('UPDATE data SET value = ?', (value,))
        connection.commit()
        self.assertTrue(Path(str(self.database) + '-wal').is_file())
        self.assertTrue(Path(str(self.database) + '-shm').is_file())

    def test_confirmed_restore_preserves_new_state_in_safety_archive(self):
        task_id = self._confirmed_task()
        result = restore_confirmed(self.root, task_id, self.database,
                                   {'service': self.config}, '1.0', self.controller)

        self.assertEqual(result['status'], 'completed')
        task = read_backup_index(self.root)['tasks'][task_id]
        self.assertEqual(task['status'], 'completed')
        self.assertEqual(task['safety_archive_id'], result['safety_archive_id'])
        with closing(sqlite3.connect(self.database)) as connection:
            self.assertEqual(connection.execute('SELECT value FROM data').fetchone(), ('old',))
        self.assertEqual(self.config.read_bytes(), b'old config')
        safety_archive = self.root / f"{result['safety_archive_id']}.zip"
        self.assertEqual(validate_backup_archive(self.root, safety_archive, '1.0')[
            'archive_id'], result['safety_archive_id'])
        snapshot = (self.root / 'safety.sqlite3').resolve()
        with zipfile.ZipFile(safety_archive) as package:
            snapshot.write_bytes(package.read('app.sqlite3'))
            self.assertEqual(package.read('configs/service.bin'), b'new config')
        with closing(sqlite3.connect(snapshot)) as connection:
            self.assertEqual(connection.execute('SELECT value FROM data').fetchone(), ('new',))
        self.controller.stop.assert_called_once_with('cu-cockpit.service')
        self.controller.start.assert_called_once_with('cu-cockpit.service')

    def test_safety_backup_failure_preserves_targets_and_resumes_service(self):
        task_id = self._confirmed_task()
        database_bytes = self.database.read_bytes()
        config_bytes = self.config.read_bytes()
        with patch('osmanager.system_management.backup_restore.create_backup_archive',
                   side_effect=OSError('safety backup failed')):
            result = restore_confirmed(self.root, task_id, self.database,
                                       {'service': self.config}, '1.0', self.controller)

        self.assertEqual(result['status'], 'failed')
        self.assertIn('safety backup failed', result['error'])
        self.assertEqual(read_backup_index(self.root)['tasks'][task_id]['status'], 'failed')
        self.assertEqual(self.database.read_bytes(), database_bytes)
        self.assertEqual(self.config.read_bytes(), config_bytes)
        self.controller.stop.assert_called_once_with('cu-cockpit.service')
        self.controller.start.assert_called_once_with('cu-cockpit.service')

    def test_config_replacement_failure_rolls_back_database_and_config(self):
        task_id = self._confirmed_task()
        self.controller.is_active.side_effect = [True, False, False, True]
        original_replace = os.replace
        config_bytes = self.config.read_bytes()
        with patch('osmanager.system_management.backup_restore.os.replace',
                   side_effect=lambda source, target: (
                       self.fail('config replacement failed') if target == self.config
                       else original_replace(source, target))) as replace:
            result = restore_confirmed(self.root, task_id, self.database,
                                       {'service': self.config}, '1.0', self.controller)

        self.assertEqual(result['status'], 'failed')
        self.assertIn('config replacement failed', result['error'])
        self.assertEqual(read_backup_index(self.root)['tasks'][task_id]['status'], 'failed')
        self.assertEqual(sum(call.args[1] == self.config for call in replace.call_args_list), 1)
        self.assertEqual(sum(call.args[1] == self.database for call in replace.call_args_list), 2)
        with closing(sqlite3.connect(self.database)) as connection:
            self.assertEqual(connection.execute('SELECT value FROM data').fetchone(), ('new',))
        self.assertEqual(self.config.read_bytes(), config_bytes)
        self.controller.stop.assert_called_once_with('cu-cockpit.service')
        self.controller.start.assert_called_once_with('cu-cockpit.service')

    def test_worker_wal_does_not_mask_rolled_back_database(self):
        with closing(sqlite3.connect(self.database)) as connection:
            connection.execute('UPDATE data SET value = ?', ('safe-current',))
            connection.commit()
        environment = patch.dict(os.environ, {'BACKUP_RESTORE_SERVICES':
                                                'cu-cockpit.service,cu-cockpit-metrics.service'})
        environment.start()
        self.addCleanup(environment.stop)
        preview = preflight_restore(self.root, self.archive['archive_id'], self.database,
                                    {'service': self.config}, '1.0', 'tester',
                                    ['cu-cockpit.service', 'cu-cockpit-metrics.service'])
        task_id = preview['task_id']
        confirm_restore(self.root, task_id, preview['token'], 'tester')
        states = {'cu-cockpit.service': True, 'cu-cockpit-metrics.service': True}
        self.controller.is_active.side_effect = lambda service: states[service]
        self.controller.stop.side_effect = lambda service: states.__setitem__(service, False)
        starts = []

        def start_service(service):
            starts.append(service)
            if service == 'cu-cockpit.service' and len(starts) == 1:
                self._write_uncheckpointed_wal('restored-worker-write')
            if service == 'cu-cockpit-metrics.service' and len(starts) == 2:
                raise OSError('another service failed to start')
            states[service] = True

        self.controller.start.side_effect = start_service
        result = restore_confirmed(self.root, task_id, self.database,
                                   {'service': self.config}, '1.0', self.controller)

        self.assertEqual(result['status'], 'failed', result)
        self.assertEqual(starts, ['cu-cockpit.service', 'cu-cockpit-metrics.service'] * 2)
        self.assertEqual(read_backup_index(self.root)['tasks'][task_id]['status'], 'failed')
        with closing(sqlite3.connect(self.database)) as connection:
            self.assertEqual(connection.execute('SELECT value FROM data').fetchone(),
                             ('safe-current',))
            self.assertEqual(connection.execute('PRAGMA integrity_check').fetchone(), ('ok',))
        self.assertFalse(Path(str(self.database) + '-wal').exists())
        self.assertFalse(Path(str(self.database) + '-shm').exists())

    def test_failed_rollback_requires_manual_recovery_without_restart(self):
        task_id = self._confirmed_task()
        self.controller.is_active.side_effect = [True, False, False]
        original_replace = os.replace
        db_replacements = []

        def fail_rollback(source, target):
            if target == self.database:
                db_replacements.append(target)
                if len(db_replacements) == 2:
                    raise OSError('safety database replacement failed')
            if target == self.config:
                raise OSError('config replacement failed')
            return original_replace(source, target)

        with patch('osmanager.system_management.backup_restore.os.replace',
                   side_effect=fail_rollback):
            result = restore_confirmed(self.root, task_id, self.database,
                                       {'service': self.config}, '1.0', self.controller)

        task = read_backup_index(self.root)['tasks'][task_id]
        self.assertEqual(len(db_replacements), 2)
        self.controller.stop.assert_called_once_with('cu-cockpit.service')
        self.controller.start.assert_not_called()
        self.assertEqual(result['status'], task['status'])
        self.assertEqual(task['status'], 'manual_recovery_required')
        self.assertTrue(result['requires_manual_recovery'])
        self.assertTrue(task['requires_manual_recovery'])
        self.assertEqual(result['safety_archive_id'], task['safety_archive_id'])
        self.assertIn('manual rollback', task['error'])
        self.assertIn(task['safety_archive_id'], task['error'])
        self.assertEqual(validate_backup_archive(
            self.root, self.root / f"{task['safety_archive_id']}.zip", '1.0')[
                'archive_id'], task['safety_archive_id'])

    def test_unsafe_sidecar_preserves_wal_and_external_file(self):
        from osmanager.system_management.backup_restore import _clear_sqlite_sidecars

        wal = Path(str(self.database) + '-wal')
        shm = Path(str(self.database) + '-shm')
        outside = self.root / 'unrelated'
        wal.write_bytes(b'pending WAL')
        outside.write_bytes(b'unrelated data')
        shm.symlink_to(outside)

        with self.assertRaisesRegex(ValueError, 'sidecar is unsafe'):
            _clear_sqlite_sidecars(self.database)

        self.assertEqual(wal.read_bytes(), b'pending WAL')
        self.assertEqual(outside.read_bytes(), b'unrelated data')
        self.assertTrue(shm.is_symlink())

    def test_backup_queue_retains_manual_recovery_task(self):
        from osmanager.system_management.backup_jobs import queue_backup

        task_id = self._confirmed_task()
        index = read_backup_index(self.root)
        index['tasks'][task_id].update(status='manual_recovery_required',
                                       requires_manual_recovery=True,
                                       safety_archive_id=self.archive['archive_id'])
        index['tasks'].update({f'old-{number}': {'status': 'failed'}
                               for number in range(255)})
        write_backup_index(self.root, index)

        self.assertEqual(queue_backup(self.root, 'later backup')['status'], 'queued')
        tasks = read_backup_index(self.root)['tasks']
        self.assertEqual(len(tasks), 256)
        self.assertTrue(tasks[task_id]['requires_manual_recovery'])
        self.assertEqual(tasks[task_id]['safety_archive_id'], self.archive['archive_id'])
        self.assertTrue((self.root / f"{self.archive['archive_id']}.zip").is_file())

    def test_wrong_token_preserves_task_state(self):
        preview = preflight_restore(self.root, self.archive['archive_id'], self.database,
                                    {'service': self.config}, '1.0', 'tester',
                                    ['cu-cockpit.service'])
        original = read_backup_index(self.root)
        with self.assertRaisesRegex(ValueError, 'confirmation rejected'):
            confirm_restore(self.root, preview['task_id'], 'wrong-token', 'tester')
        self.assertEqual(read_backup_index(self.root), original)

    def test_consumed_confirmation_token_cannot_be_replayed(self):
        preview = preflight_restore(self.root, self.archive['archive_id'], self.database,
                                    {'service': self.config}, '1.0', 'tester',
                                    ['cu-cockpit.service'])
        confirm_restore(self.root, preview['task_id'], preview['token'], 'tester')
        original = read_backup_index(self.root)
        with self.assertRaisesRegex(ValueError, 'confirmation rejected'):
            confirm_restore(self.root, preview['task_id'], preview['token'], 'tester')
        self.assertEqual(read_backup_index(self.root), original)
