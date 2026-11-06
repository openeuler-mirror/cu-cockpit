"""Maintenance-only restore workflow for registered local backup targets."""

import hashlib
import os
import re
import stat
from pathlib import Path

from .backup_center import (MAX_ARCHIVE_BYTES, MAX_CONFIG_TARGETS, read_backup_index,
                            validate_backup_archive)


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