import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from osmanager.system_management.backup_center import (
    backup_lock, backup_sqlite, initialize_installation, read_backup_index, verify_sqlite,
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
