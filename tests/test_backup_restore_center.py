import json
import sqlite3
import tempfile
import unittest
import warnings
import zipfile
from contextlib import closing
from pathlib import Path

from osmanager.system_management.backup_center import (
    backup_lock, backup_sqlite, create_backup_archive, import_backup_archive,
    initialize_installation, read_backup_index, validate_backup_archive, verify_sqlite,
    write_backup_index,
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
