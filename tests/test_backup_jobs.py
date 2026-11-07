import sqlite3
import tempfile
import unittest
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from osmanager.system_management.backup_center import (
    backup_lock, initialize_installation, read_backup_index, validate_backup_archive,
    write_backup_index,
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

    def test_worker_leaves_running_and_queued_restore_tasks_untouched(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            initialize_installation(root, '1.0')
            running = {'id': 'a' * 32, 'kind': 'restore', 'status': 'running'}
            queued = {'id': 'b' * 32, 'kind': 'restore', 'status': 'queued'}
            index = {'tasks': {running['id']: running, queued['id']: queued}, 'backups': {}}
            write_backup_index(root, index)

            with patch('osmanager.system_management.backup_jobs.create_backup_archive') as create:
                self.assertIsNone(run_pending(root, root / 'missing.sqlite3', {}, '1.0'))
            create.assert_not_called()
            self.assertEqual(read_backup_index(root), index)

    def test_list_skips_restore_without_created_at_and_keeps_legacy_backups(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            initialize_installation(root, '1.0')
            restore = {'id': 'a' * 32, 'kind': 'restore', 'status': 'queued'}
            legacy = {'id': 'b' * 32, 'status': 'failed', 'created_at': '2026-01-01'}
            current = {'id': 'c' * 32, 'kind': 'backup', 'status': 'queued',
                       'created_at': '2026-01-02'}
            index = {'tasks': {restore['id']: restore, legacy['id']: legacy,
                               current['id']: current}, 'backups': {}}
            write_backup_index(root, index)

            self.assertEqual(list_backup_tasks(root), [current, legacy])

    def test_manual_queue_full_reclaims_only_backup_and_keeps_restore_recovery(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            initialize_installation(root, '1.0')
            failed_restore = {'id': 'a' * 32, 'kind': 'restore', 'status': 'failed'}
            recovery = {'id': 'b' * 32, 'kind': 'restore',
                        'status': 'manual_recovery_required', 'requires_manual_recovery': True,
                        'safety_archive_id': 'c' * 32}
            tasks = {failed_restore['id']: failed_restore, recovery['id']: recovery}
            tasks.update({f'pending-{number}': {'status': 'queued'} for number in range(253)})
            tasks['old-backup'] = {'status': 'failed'}
            write_backup_index(root, {'tasks': tasks, 'backups': {}})

            new_task = queue_backup(root, 'creator')
            updated = read_backup_index(root)['tasks']
            self.assertEqual(len(updated), 256)
            self.assertEqual(updated[failed_restore['id']], failed_restore)
            self.assertEqual(updated[recovery['id']], recovery)
            self.assertNotIn('old-backup', updated)
            self.assertEqual(updated[new_task['id']]['kind'], 'backup')

    def test_due_daily_backup_queues_once_per_slot(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            initialize_installation(root, '1.0')
            save_backup_schedule(root, True, '02:00')
            due = datetime(2026, 1, 2, 2, 0, tzinfo=timezone.utc)

            task = queue_due_backup(root, due)
            self.assertEqual(task['status'], 'queued')
            self.assertEqual(task['actor'], 'daily-schedule')
            self.assertEqual(read_backup_schedule(root)['last_slot'], '2026-01-02')
            before = read_backup_index(root)
            self.assertIsNone(queue_due_backup(root, due))
            self.assertIsNone(queue_due_backup(
                root, datetime(2026, 1, 2, 23, 0, tzinfo=timezone.utc)))
            self.assertEqual(read_backup_index(root), before)
            self.assertEqual(list_backup_tasks(root), [task])

    def test_disabled_daily_backup_does_not_queue(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            initialize_installation(root, '1.0')
            save_backup_schedule(root, False, '02:00')
            due = datetime(2026, 1, 2, 2, 0, tzinfo=timezone.utc)

            self.assertIsNone(queue_due_backup(root, due))
            self.assertEqual(list_backup_tasks(root), [])
            self.assertIsNone(read_backup_schedule(root)['last_slot'])

    def test_invalid_schedule_time_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            initialize_installation(root, '1.0')

            for value in ('24:00', '2:00'):
                with self.subTest(value=value):
                    with self.assertRaisesRegex(ValueError, 'Invalid backup schedule settings'):
                        save_backup_schedule(root, True, value)
            self.assertFalse((root / 'schedule.json').exists())

    def test_non_boolean_schedule_enabled_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            initialize_installation(root, '1.0')

            for value in (1, 'true', None):
                with self.subTest(value=value):
                    with self.assertRaisesRegex(ValueError, 'Invalid backup schedule settings'):
                        save_backup_schedule(root, value, '02:00')
            self.assertFalse((root / 'schedule.json').exists())

    def test_next_run_uses_schedule_timezone(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            initialize_installation(root, '1.0')
            save_backup_schedule(root, True, '02:00', 'Asia/Shanghai')

            before = datetime(2026, 1, 2, 17, 0, tzinfo=timezone.utc)
            after = datetime(2026, 1, 2, 19, 0, tzinfo=timezone.utc)
            self.assertEqual(read_backup_schedule(root, before)['next_run'],
                             '2026-01-03T02:00:00+08:00')
            self.assertEqual(read_backup_schedule(root, after)['next_run'],
                             '2026-01-04T02:00:00+08:00')
