"""Local backup maintenance and scheduled worker entry point."""

import json
import os
import subprocess

from django.db import connections
from django.core.management.base import BaseCommand, CommandError

from osmanager.system_management.backup_center import (
    initialize_backup_root, initialize_installation, update_installation_version,
    write_backup_index,
)
from osmanager.system_management.backup_jobs import (
    queue_due_backup, run_pending, write_backup_schedule,
)
from osmanager.system_management.backup_restore import RESTORE_UNITS, restore_confirmed
from osmanager.system_management.backup_runtime import (
    BACKUP_COMPAT_VERSION, backup_configs, backup_database, backup_location,
    require_installation,
)


def _require_root(root=None):
    if os.geteuid() != 0:
        raise PermissionError('Backup maintenance requires root privileges')
    if root is not None and root.stat().st_uid != 0:
        raise PermissionError('Backup root must be owned by root')


class SystemdController:
    """Only operate the locally registered application writers."""

    @staticmethod
    def _invoke(*args):
        if args[-1] not in RESTORE_UNITS:
            raise ValueError('Unregistered restore unit')
        return subprocess.run(['systemctl', *args], capture_output=True, text=True,
                              check=False, timeout=30)

    def is_active(self, unit):
        state = self._invoke('show', '--property=ActiveState', '--value', unit)
        probe = self._invoke('is-active', unit)
        if state.returncode or state.stdout.strip() not in ('active', 'inactive'):
            raise RuntimeError(f'Cannot verify restore unit state: {unit}')
        current = state.stdout.strip()
        if (probe.returncode, probe.stdout.strip()) != (
                (0, 'active') if current == 'active' else (3, 'inactive')):
            raise RuntimeError(f'Conflicting restore unit state: {unit}')
        return current

    def stop(self, unit):
        result = self._invoke('stop', unit)
        if result.returncode:
            raise RuntimeError(f'Cannot stop restore unit: {unit}')

    def start(self, unit):
        result = self._invoke('start', unit)
        if result.returncode:
            raise RuntimeError(f'Cannot start restore unit: {unit}')


class Command(BaseCommand):
    help = 'Initialize and operate the local backup center'

    def add_arguments(self, parser):
        parser.add_argument('action', choices=(
            'init', 'upgrade-version', 'run-pending', 'run-scheduled', 'restore'))
        parser.add_argument('task_id', nargs='?')
        parser.add_argument('--confirm-maintenance', action='store_true')
        parser.add_argument('--from-version')

    def handle(self, *args, **options):
        try:
            action = options['action']
            if (action == 'restore') != bool(options['task_id']):
                raise ValueError('Task ID is required only for restore')
            if action != 'restore' and options['confirm_maintenance']:
                raise ValueError('Maintenance confirmation is only for restore')
            if action == 'restore' and not options['confirm_maintenance']:
                raise ValueError('Restore requires --confirm-maintenance')
            if action == 'restore' and os.environ.get('INVOCATION_ID'):
                raise ValueError('Restore requires an independent SSH maintenance process')
            if (action == 'upgrade-version') != bool(options['from_version']):
                raise ValueError('--from-version is required only for upgrade-version')
            _require_root()
            if action == 'init':
                root = initialize_backup_root(backup_location())
                _require_root(root)
                identity = initialize_installation(root, BACKUP_COMPAT_VERSION)
                if not os.path.lexists(root / 'index.json'):
                    write_backup_index(root, {'tasks': {}, 'backups': {}})
                if not os.path.lexists(root / 'schedule.json'):
                    write_backup_schedule(root, {'enabled': False, 'time': '02:00',
                                                 'timezone': 'UTC', 'last_slot': None})
                result = {'installation_id': identity['installation_id']}
            elif action == 'upgrade-version':
                root = backup_location()
                _require_root(root)
                identity = update_installation_version(
                    root, options['from_version'], BACKUP_COMPAT_VERSION)
                result = {'installation_id': identity['installation_id'],
                          'application_version': identity['application_version']}
            else:
                root = require_installation()
                _require_root(root)
                if action == 'restore':
                    database = backup_database()
                    configs = backup_configs()
                    connections.close_all()
                    result = restore_confirmed(root, options['task_id'], database,
                                               configs, BACKUP_COMPAT_VERSION,
                                               SystemdController())
                else:
                    database = backup_database()
                    configs = backup_configs()
                    if action == 'run-scheduled':
                        queue_due_backup(root)
                    result = run_pending(root, database, configs, BACKUP_COMPAT_VERSION)
            self.stdout.write(json.dumps(result, allow_nan=False))
            if isinstance(result, dict) and result.get('status') in (
                    'failed', 'manual_recovery_required'):
                raise CommandError(f'Backup task {result["id"]} {result["status"]}')
        except (OSError, ValueError, RuntimeError) as error:
            raise CommandError(str(error)) from error
