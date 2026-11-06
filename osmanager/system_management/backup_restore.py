"""Maintenance-only restore workflow for registered local backup targets."""

import hashlib
import hmac
import json
import os
import re
import secrets
import stat
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .backup_center import (MAX_ARCHIVE_BYTES, MAX_CONFIG_TARGETS, read_backup_index,
                            backup_lock, validate_backup_archive, write_backup_index)


def _restore_targets(db_path: Path, configs: dict) -> dict:
    if not isinstance(configs, dict) or len(configs) > MAX_CONFIG_TARGETS:
        raise ValueError('Invalid restore configuration registry')
    targets = {'app.sqlite3': db_path}
    for name, path in configs.items():
        if not isinstance(name, str) or not name or not name.replace('_', '').replace('-', '').isalnum() or len(name) > 48:
            raise ValueError('Invalid restore configuration name')
        targets[f'configs/{name}.bin'] = path
    if len(set(targets.values())) != len(targets):
        raise ValueError('Restore targets must be distinct')
    for path in targets.values():
        if not isinstance(path, Path) or not path.is_absolute() or '..' in path.parts:
            raise ValueError('Restore target must be an absolute registered path')
        for parent in path.parents:
            details = parent.lstat()
            if not stat.S_ISDIR(details.st_mode) or (
                    details.st_mode & 0o022 and not details.st_mode & stat.S_ISVTX):
                raise ValueError('Restore parent is unsafe')
        details = path.lstat()
        if not stat.S_ISREG(details.st_mode) or details.st_nlink != 1:
            raise ValueError('Restore target must be an unlinked regular file')
    return {name: str(path) for name, path in targets.items()}


def _registered_archive(root: Path, archive_id: str, version: str) -> tuple:
    if not isinstance(archive_id, str) or not re.fullmatch(r'[0-9a-f]{32}', archive_id):
        raise ValueError('Invalid registered archive ID')
    index = read_backup_index(root)
    record = index['backups'].get(archive_id)
    if not isinstance(record, dict) or record.get('archive_id') != archive_id:
        raise ValueError('Archive is not registered')
    path = root / f'{archive_id}.zip'
    manifest = validate_backup_archive(root, path, version)
    if manifest['archive_id'] != archive_id or record['size'] != path.stat().st_size:
        raise ValueError('Registered archive has changed')
    digest = hashlib.sha256()
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, 'rb') as archive:
        if os.fstat(archive.fileno()).st_size > MAX_ARCHIVE_BYTES:
            raise ValueError('Registered archive is too large')
        for chunk in iter(lambda: archive.read(1024 * 1024), b''):
            digest.update(chunk)
    return manifest, digest.hexdigest()


def _restore_services(services) -> list:
    allowed = {'cu-cockpit.service', 'cu-cockpit-metrics.service',
               'cu-cockpit-metrics.timer', 'cu-cockpit-inspection.service',
               'cu-cockpit-inspection.timer'}
    configured = set(filter(None, os.environ.get('BACKUP_RESTORE_SERVICES', '').split(',')))
    if not configured or not configured <= allowed:
        raise ValueError('Restore services are not safely configured')
    if (not isinstance(services, (list, tuple)) or not services or
            len(services) != len(set(services)) or set(services) != configured or
            not all(isinstance(service, str) for service in services)):
        raise ValueError('Restore services must match the local registry')
    return sorted(configured)


def _token_digest(token: str, task: dict) -> str:
    binding = {name: task[name] for name in (
        'archive_id', 'archive_hash', 'version', 'actor', 'targets', 'services')}
    payload = json.dumps(binding, sort_keys=True, separators=(',', ':')).encode('utf-8')
    return hashlib.sha256(token.encode('ascii') + payload).hexdigest()


def preflight_restore(root: Path, archive_id: str, db_path: Path, configs: dict,
                      version: str, actor: str, services) -> dict:
    if not isinstance(actor, str) or not actor or len(actor) > 128:
        raise ValueError('Invalid restore actor')
    targets = _restore_targets(db_path, configs)
    stopped = _restore_services(services)
    with backup_lock(root):
        manifest, archive_hash = _registered_archive(root, archive_id, version)
        if set(manifest['members']) != set(targets):
            raise ValueError('Archive members differ from registered targets')
        index = read_backup_index(root)
        if len(index['tasks']) >= 256:
            raise ValueError('Restore task history is full')
        token = secrets.token_urlsafe(32)
        task_id = secrets.token_hex(16)
        task = {'id': task_id, 'kind': 'restore', 'archive_id': archive_id,
                'archive_hash': archive_hash, 'version': version, 'actor': actor,
                'targets': targets, 'services': stopped, 'status': 'awaiting_confirmation',
                'expires_at': (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat()}
        task['token_hash'] = _token_digest(token, task)
        index['tasks'][task_id] = task
        write_backup_index(root, index, locked=True)
    return {'task_id': task_id, 'token': token, 'expires_at': task['expires_at'],
            'preview': {'members': manifest['members'],
                        'total_size': sum(member['size'] for member in manifest['members'].values()),
                        'targets': [path.name for path in (db_path, *configs.values())],
                        'services': stopped, 'requires_maintenance': True,
                        'risks': ['Service downtime', 'Database and configuration replacement',
                                  'Existing sessions invalidated']}}


def confirm_restore(root: Path, task_id: str, token: str, actor: str) -> dict:
    if not isinstance(task_id, str) or not re.fullmatch(r'[0-9a-f]{32}', task_id):
        raise ValueError('Invalid restore task ID')
    with backup_lock(root):
        index = read_backup_index(root)
        task = index['tasks'].get(task_id)
        if (not isinstance(task, dict) or task.get('kind') != 'restore' or
                task.get('status') != 'awaiting_confirmation' or task.get('actor') != actor or
                not isinstance(token, str) or not token.isascii() or
                len(token) > 128 or
                datetime.fromisoformat(task['expires_at']) <= datetime.now(timezone.utc) or
                not hmac.compare_digest(task['token_hash'], _token_digest(token, task))):
            raise ValueError('Restore confirmation rejected')
        task['status'] = 'awaiting_maintenance'
        task.pop('token_hash')
        task['confirmed_at'] = datetime.now(timezone.utc).isoformat()
        write_backup_index(root, index, locked=True)
        return {'id': task_id, 'status': task['status']}


def _resume_services(controller, active: list) -> None:
    failed = []
    for service in reversed(active):
        try:
            controller.start(service)
            if not controller.is_active(service):
                failed.append(service)
        except Exception:
            failed.append(service)
    if failed:
        raise RuntimeError(f'Manual service restart required: {", ".join(failed)}')


def _pause_services(controller, services: list) -> list:
    active = []
    try:
        for service in services:
            was_active = controller.is_active(service)
            if was_active:
                active.append(service)
                controller.stop(service)
            if controller.is_active(service):
                raise RuntimeError('Restore service remains active')
    except Exception:
        try:
            _resume_services(controller, active)
        except Exception as restart_error:
            raise RuntimeError('Service shutdown failed; manual restart required') from restart_error
        raise
    return active