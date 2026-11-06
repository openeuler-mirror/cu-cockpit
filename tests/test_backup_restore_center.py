import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from osmanager.system_management.backup_center import backup_sqlite, initialize_installation, verify_sqlite


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
