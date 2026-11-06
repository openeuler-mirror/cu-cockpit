import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

from osmanager.system_management.backup_center import (
    backup_lock, initialize_installation, read_backup_index, validate_backup_archive,
)
from osmanager.system_management.backup_jobs import (
    get_backup_task, list_backup_tasks, queue_backup, queue_due_backup, read_backup_schedule,
    run_pending, save_backup_schedule,
)


class BackupJobsTest(unittest.TestCase):
    def test_queue_runs_once_and_publishes_archive(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            initialize_installation(root, '1.0')
            database = root / 'app.sqlite3'
            with closing(sqlite3.connect(database)) as connection:
                connection.execute('CREATE TABLE data (value INTEGER)')
                connection.commit()
            job = queue_backup(root, 'creator')
            self.assertEqual(list_backup_tasks(root), [job])

            completed = run_pending(root, database, {}, '1.0')
            self.assertEqual(completed['status'], 'succeeded')
            self.assertEqual(get_backup_task(root, job['id']), completed)
            self.assertEqual(completed['result'], read_backup_index(root)['backups'][
                completed['archive_id']])
            archive = root / f'{completed["archive_id"]}.zip'
            self.assertEqual(validate_backup_archive(root, archive, '1.0')['archive_id'],
                             completed['archive_id'])
            self.assertIsNone(run_pending(root, database, {}, '1.0'))

    def test_worker_failure_records_failed_without_archive(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            initialize_installation(root, '1.0')
            database = root / 'app.sqlite3'
            with closing(sqlite3.connect(database)) as connection:
                connection.execute('CREATE TABLE data (value INTEGER)')
                connection.commit()
            job = queue_backup(root, 'creator')

            with patch('osmanager.system_management.backup_jobs.create_backup_archive',
                       side_effect=RuntimeError('private failure')):
                failed = run_pending(root, database, {}, '1.0')
            self.assertEqual(failed['status'], 'failed')
            self.assertEqual(failed['error'], 'Backup operation failed')
            self.assertEqual(get_backup_task(root, job['id']), failed)
            self.assertEqual(read_backup_index(root)['backups'], {})
            self.assertEqual(list(root.glob('*.zip')), [])

    def test_running_with_held_lock_rejects_without_changing_queue(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            initialize_installation(root, '1.0')
            database = root / 'app.sqlite3'
            with closing(sqlite3.connect(database)) as connection:
                connection.execute('CREATE TABLE data (value INTEGER)')
                connection.commit()
            job = queue_backup(root, 'creator')
            before = read_backup_index(root)

            with backup_lock(root):
                with self.assertRaises(BlockingIOError):
                    run_pending(root, database, {}, '1.0')
            self.assertEqual(get_backup_task(root, job['id']), job)
            self.assertEqual(read_backup_index(root), before)
            self.assertEqual(list(root.glob('*.zip')), [])
