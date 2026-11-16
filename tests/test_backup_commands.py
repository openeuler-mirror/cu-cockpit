"""Local maintenance commands without host services or deployment targets."""

import io
import json
import os
import sqlite3
import subprocess
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.core.management import call_command
from django.core.management.base import CommandError

from osmanager.system_management.backup_center import (
    create_backup_archive, initialize_installation, read_backup_index, write_backup_index,
)
from osmanager.system_management.backup_jobs import (
    queue_backup, read_backup_schedule, save_backup_schedule,
)
from osmanager.system_management.backup_restore import confirm_restore, preflight_restore
from osmanager.system_management.backup_runtime import BACKUP_COMPAT_VERSION
from osmanager.system_management.management.commands.backup_center import (
    SystemdController, _require_root,
)


class BackupCommandTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name).resolve()
        self.root = self.directory / 'backups'
        self.database = self.directory / 'app.sqlite3'
        with closing(sqlite3.connect(self.database)) as database:
            database.execute('CREATE TABLE data (value TEXT)')
            database.execute('INSERT INTO data VALUES (?)', ('saved',))
            database.commit()
        self.config = self.directory / 'chrony.conf'
        self.config.write_text('pool example.invalid\n', encoding='utf-8')
        self.enterContext(patch.dict(os.environ, {'BACKUP_ROOT': str(self.root),
                                                'BACKUP_RESTORE_SERVICES': 'cu-cockpit.service'}))
        self.enterContext(patch(
            'osmanager.system_management.management.commands.backup_center._require_root'))
        self.enterContext(patch(
            'osmanager.system_management.management.commands.backup_center.backup_database',
            return_value=self.database))
        self.enterContext(patch(
            'osmanager.system_management.management.commands.backup_center.backup_configs',
            return_value={'chrony': self.config}))
        units = self.directory / 'units'
        units.mkdir()
        (units / 'cu-cockpit.service').touch()
        self.units = units
        self.enterContext(patch('osmanager.system_management.backup_restore.SYSTEMD_UNIT_DIRS',
                                (units,)))

    def command(self, *arguments):
        output = io.StringIO()
        call_command('backup_center', *arguments, stdout=output)
        return json.loads(output.getvalue())

    def test_init_is_explicit_private_and_does_not_replace_identity(self):
        first = self.command('init')
        key = json.loads((self.root / 'metadata.json').read_text())['hmac_key']
        task = queue_backup(self.root, 'tester')
        save_backup_schedule(self.root, True, '03:00')
        self.assertEqual(self.command('init'), first)
        self.assertEqual(json.loads((self.root / 'metadata.json').read_text())['hmac_key'], key)
        self.assertIn(task['id'], read_backup_index(self.root)['tasks'])
        self.assertTrue(read_backup_schedule(self.root)['enabled'])
        self.assertEqual(self.root.stat().st_mode & 0o777, 0o700)
        for name in ('metadata.json', 'index.json', 'schedule.json'):
            self.assertEqual((self.root / name).stat().st_mode & 0o777, 0o600)
        self.assertNotIn(key, json.dumps(first))

    def test_upgrade_preserves_key_and_requires_explicit_prior_version(self):
        self.root.mkdir(mode=0o700)
        original = initialize_installation(self.root, 'old')
        with self.assertRaises(CommandError):
            self.command('init')
        with self.assertRaises(CommandError):
            self.command('upgrade-version')
        upgraded = self.command('upgrade-version', '--from-version', 'old')
        self.assertEqual(upgraded['installation_id'], original['installation_id'])
        self.assertEqual(json.loads((self.root / 'metadata.json').read_text())['hmac_key'],
                         original['hmac_key'])
        self.assertEqual(upgraded['application_version'], BACKUP_COMPAT_VERSION)

    def test_pending_success_failure_and_due_schedule(self):
        self.command('init')
        queued = queue_backup(self.root, 'tester')
        result = self.command('run-pending')
        self.assertEqual(result['id'], queued['id'])
        self.assertEqual(result['status'], 'succeeded')
        self.assertIsNone(self.command('run-pending'))
        save_backup_schedule(self.root, True, '00:00')
        scheduled = self.command('run-scheduled')
        self.assertEqual(scheduled['actor'], 'daily-schedule')
        self.assertEqual(scheduled['status'], 'succeeded')
        self.assertIsNone(self.command('run-scheduled'))
        queued = queue_backup(self.root, 'failure')
        with patch('osmanager.system_management.backup_jobs.create_backup_archive',
                   side_effect=OSError('private')):
            output = io.StringIO()
            with self.assertRaises(CommandError):
                call_command('backup_center', 'run-pending', stdout=output)
        self.assertEqual(json.loads(output.getvalue())['id'], queued['id'])
        self.assertEqual(json.loads(output.getvalue())['status'], 'failed')
        self.assertEqual(read_backup_index(self.root)['tasks'][queued['id']]['status'], 'failed')

    def test_restore_rejects_missing_flag_and_invalid_task_before_stop(self):
        self.command('init')
        controller = Mock()
        with patch('osmanager.system_management.management.commands.backup_center.SystemdController',
                   return_value=controller):
            with self.assertRaises(CommandError):
                self.command('restore', 'a' * 32)
            with self.assertRaises(CommandError):
                self.command('restore', 'invalid', '--confirm-maintenance')
            with self.assertRaises(CommandError):
                self.command('restore', 'a' * 32, '--confirm-maintenance')
            with patch.dict(os.environ, {'INVOCATION_ID': 'service-process'}):
                with self.assertRaisesRegex(CommandError, 'independent SSH'):
                    self.command('restore', 'a' * 32, '--confirm-maintenance')
        controller.stop.assert_not_called()

    def test_unconfirmed_and_expired_tasks_do_not_stop_services(self):
        self.command('init')
        archive = create_backup_archive(self.root, self.database,
                                        {'chrony': self.config}, BACKUP_COMPAT_VERSION, 'user')
        preview = preflight_restore(self.root, archive['archive_id'], self.database,
                                    {'chrony': self.config}, BACKUP_COMPAT_VERSION, 'user',
                                    ['cu-cockpit.service'])
        controller = Mock()
        with patch('osmanager.system_management.management.commands.backup_center.SystemdController',
                   return_value=controller):
            with self.assertRaises(CommandError):
                self.command('restore', preview['task_id'], '--confirm-maintenance')
            confirm_restore(self.root, preview['task_id'], preview['token'], 'user')
            index = read_backup_index(self.root)
            index['tasks'][preview['task_id']]['expires_at'] = '2000-01-01T00:00:00+00:00'
            write_backup_index(self.root, index)
            with self.assertRaises(CommandError):
                self.command('restore', preview['task_id'], '--confirm-maintenance')
        controller.stop.assert_not_called()

    def test_root_privileges_and_ownership_are_required(self):
        with patch('osmanager.system_management.management.commands.backup_center.os.geteuid',
                   return_value=1000):
            with self.assertRaises(PermissionError):
                _require_root()
        self.root.mkdir(mode=0o700)
        with patch('osmanager.system_management.management.commands.backup_center.os.geteuid',
                   return_value=0):
            with patch.object(Path, 'stat', return_value=SimpleNamespace(st_uid=1000)):
                with self.assertRaises(PermissionError):
                    _require_root(self.root)

    def test_confirmed_restore_runs_only_through_fake_controller(self):
        self.command('init')
        archive = create_backup_archive(self.root, self.database,
                                        {'chrony': self.config}, BACKUP_COMPAT_VERSION, 'user')
        with closing(sqlite3.connect(self.database)) as database:
            database.execute('UPDATE data SET value = ?', ('new',))
            database.commit()
        preview = preflight_restore(self.root, archive['archive_id'], self.database,
                                    {'chrony': self.config}, BACKUP_COMPAT_VERSION, 'user',
                                    ['cu-cockpit.service'])
        confirm_restore(self.root, preview['task_id'], preview['token'], 'user')
        states = {'cu-cockpit.service': 'active'}
        controller = Mock()
        controller.is_active.side_effect = lambda unit: states[unit]
        controller.stop.side_effect = lambda unit: states.__setitem__(unit, 'inactive')
        controller.start.side_effect = lambda unit: states.__setitem__(unit, 'active')
        with patch('osmanager.system_management.management.commands.backup_center.SystemdController',
                   return_value=controller), patch('django.db.connections.close_all') as close:
            result = self.command('restore', preview['task_id'], '--confirm-maintenance')
        close.assert_called_once()
        self.assertEqual(result['status'], 'completed')
        self.assertEqual(read_backup_index(self.root)['tasks'][preview['task_id']]['status'],
                         'completed')
        controller.stop.assert_called_once_with('cu-cockpit.service')
        with closing(sqlite3.connect(self.database)) as database:
            self.assertEqual(database.execute('SELECT value FROM data').fetchone(), ('saved',))

    def _multi_unit_restore(self):
        services = ('cu-cockpit.service', 'cu-cockpit-metrics.service',
                    'cu-cockpit-backup.timer')
        self.enterContext(patch.dict(os.environ, {'BACKUP_RESTORE_SERVICES': ','.join(services)}))
        for service in services:
            (self.units / service).touch()
        self.command('init')
        archive = create_backup_archive(self.root, self.database,
                                        {'chrony': self.config}, BACKUP_COMPAT_VERSION, 'user')
        with closing(sqlite3.connect(self.database)) as database:
            database.execute('UPDATE data SET value = ?', ('new',))
            database.commit()
        preview = preflight_restore(self.root, archive['archive_id'], self.database,
                                    {'chrony': self.config}, BACKUP_COMPAT_VERSION, 'user',
                                    services)
        confirm_restore(self.root, preview['task_id'], preview['token'], 'user')
        return preview['task_id'], services

    def _restore_with_failed_timer(self, *, query_failure=False):
        task_id, services = self._multi_unit_restore()
        states = dict.fromkeys(services, 'active')
        calls = []
        probes = dict.fromkeys(services, 0)

        def systemctl(argv, **kwargs):
            self.assertEqual(argv[0], 'systemctl')
            self.assertIn(argv[-1], services)
            self.assertNotIn('shell', kwargs)
            calls.append((argv[1], argv[-1]))
            action, service = argv[1], argv[-1]
            if action == 'show':
                probes[service] += 1
                if query_failure and service == 'cu-cockpit-metrics.service' and probes[service] == 4:
                    return subprocess.CompletedProcess(argv, 1, '')
                return subprocess.CompletedProcess(argv, 0, states[service] + '\n')
            if action == 'is-active':
                state = states[service]
                return subprocess.CompletedProcess(argv, 0 if state == 'active' else 3,
                                                   state + '\n')
            if action == 'stop':
                states[service] = 'inactive'
                return subprocess.CompletedProcess(argv, 0, '')
            if action == 'start':
                if service == 'cu-cockpit-backup.timer':
                    states[service] = 'failed'
                    return subprocess.CompletedProcess(argv, 1, '')
                states[service] = 'active'
                return subprocess.CompletedProcess(argv, 0, '')
            self.fail(f'Unexpected systemctl action: {action}')

        output = io.StringIO()
        with patch('osmanager.system_management.management.commands.backup_center.subprocess.run',
                   side_effect=systemctl):
            with self.assertRaises(CommandError):
                call_command('backup_center', 'restore', task_id,
                             '--confirm-maintenance', stdout=output)
        result = json.loads(output.getvalue())
        task = read_backup_index(self.root)['tasks'][task_id]
        self.assertEqual(result['status'], 'manual_recovery_required')
        self.assertEqual(task['status'], result['status'])
        self.assertTrue(task['requires_manual_recovery'])
        self.assertEqual(task['safety_archive_id'], result['safety_archive_id'])
        self.assertTrue((self.root / f"{task['safety_archive_id']}.zip").is_file())
        self.assertIn(('start', 'cu-cockpit.service'), calls)
        self.assertIn(('start', 'cu-cockpit-backup.timer'), calls)
        self.assertTrue(all(state != 'active' for state in states.values()), states)
        self.assertEqual({service for action, service in calls if action == 'stop'},
                         set(services))
        return task, states, calls

    def test_failed_timer_restart_stops_all_writers_and_rolls_back(self):
        task, states, calls = self._restore_with_failed_timer()
        self.assertEqual(set(states.values()), {'inactive'})
        self.assertIn('manual service restart', task['error'])
        self.assertEqual(sum(action == 'start' for action, _ in calls), 3)
        with closing(sqlite3.connect(self.database)) as database:
            self.assertEqual(database.execute('SELECT value FROM data').fetchone(), ('new',))

    def test_failed_cleanup_query_does_not_skip_other_writer_stops(self):
        task, states, calls = self._restore_with_failed_timer(query_failure=True)
        self.assertIn('cu-cockpit-metrics.service', task['error'])
        self.assertIn(('stop', 'cu-cockpit.service'), calls)
        self.assertEqual(states['cu-cockpit.service'], 'inactive')
        with closing(sqlite3.connect(self.database)) as database:
            self.assertEqual(database.execute('SELECT value FROM data').fetchone(), ('saved',))

    def test_unknown_service_state_fails_restore_without_stopping_or_starting(self):
        self.command('init')
        archive = create_backup_archive(self.root, self.database,
                                        {'chrony': self.config}, BACKUP_COMPAT_VERSION, 'user')
        preview = preflight_restore(self.root, archive['archive_id'], self.database,
                                    {'chrony': self.config}, BACKUP_COMPAT_VERSION, 'user',
                                    ['cu-cockpit.service'])
        confirm_restore(self.root, preview['task_id'], preview['token'], 'user')
        controller = Mock()
        controller.is_active.return_value = 'unknown'
        output = io.StringIO()
        with patch('osmanager.system_management.management.commands.backup_center.SystemdController',
                   return_value=controller):
            with self.assertRaises(CommandError):
                call_command('backup_center', 'restore', preview['task_id'],
                             '--confirm-maintenance', stdout=output)
        self.assertEqual(json.loads(output.getvalue())['status'], 'failed')
        self.assertEqual(read_backup_index(self.root)['tasks'][preview['task_id']]['status'],
                         'failed')
        controller.stop.assert_not_called()
        controller.start.assert_not_called()

    def test_missing_registered_config_is_a_worker_error(self):
        self.command('init')
        with patch('osmanager.system_management.management.commands.backup_center.backup_configs',
                   side_effect=FileNotFoundError('Chrony is unavailable')):
            with self.assertRaisesRegex(CommandError, 'Chrony is unavailable'):
                self.command('run-pending')


class SystemdControllerTest(unittest.TestCase):
    def test_only_fixed_units_and_exact_active_states(self):
        controller = SystemdController()
        with patch('osmanager.system_management.management.commands.backup_center.subprocess.run') as run:
            run.side_effect = [SimpleNamespace(returncode=0, stdout='inactive\n'),
                               SimpleNamespace(returncode=3, stdout='inactive\n')]
            self.assertEqual(controller.is_active('cu-cockpit.service'), 'inactive')
            self.assertEqual(run.call_args_list[0].args[0],
                             ['systemctl', 'show', '--property=ActiveState', '--value',
                              'cu-cockpit.service'])
            self.assertEqual(run.call_args_list[1].args[0],
                             ['systemctl', 'is-active', 'cu-cockpit.service'])
            self.assertTrue(all(call.kwargs['timeout'] == 30 for call in run.call_args_list))
            run.reset_mock()
            with self.assertRaises(ValueError):
                controller.stop('ssh.service; reboot')
            run.assert_not_called()
            for state in ('unknown', 'activating', 'deactivating', 'failed'):
                run.side_effect = [SimpleNamespace(returncode=0, stdout=state + '\n'),
                                   SimpleNamespace(returncode=3, stdout=state + '\n')]
                with self.assertRaises(RuntimeError):
                    controller.is_active('cu-cockpit.service')

    def test_stop_failure_is_not_ignored(self):
        with patch('osmanager.system_management.management.commands.backup_center.subprocess.run',
                   return_value=SimpleNamespace(returncode=1)):
            with self.assertRaises(RuntimeError):
                SystemdController().stop('cu-cockpit.service')


class BackupInstallerTest(unittest.TestCase):
    def test_rendered_unit_and_unsafe_app_path(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory).resolve()
            script = Path(__file__).resolve().parents[1] / 'packaging/rpm/install_backup_timer.sh'
            unit_dir = base / 'units'
            app_dir = base / 'application'
            env = {**os.environ, 'SYSTEMD_UNIT_DIR': str(unit_dir),
                   'APP_DIR': str(app_dir), 'SKIP_SYSTEMCTL': 'true'}
            installed = subprocess.run(['bash', str(script)], env=env, capture_output=True,
                                       text=True, check=False)
            self.assertEqual(installed.returncode, 0, installed.stderr)
            service = (unit_dir / 'cu-cockpit-backup.service').read_text()
            timer = (unit_dir / 'cu-cockpit-backup.timer').read_text()
            self.assertIn(f'EnvironmentFile={app_dir}/os.env', service)
            self.assertIn(f'ExecStart={app_dir}/venv/bin/python {app_dir}/manage.py '
                          'backup_center run-scheduled', service)
            self.assertIn('TimeoutStartSec=180', service)
            self.assertIn('KillMode=control-group', service)
            self.assertIn('OnUnitActiveSec=1min', timer)
            self.assertFalse((app_dir / 'var/backups').exists())
            rejected = subprocess.run(['bash', str(script)],
                                      env={**env, 'APP_DIR': '/tmp/../unsafe'},
                                      capture_output=True, text=True, check=False)
            self.assertEqual(rejected.returncode, 2)
            self.assertIn('safe absolute path', rejected.stderr)
