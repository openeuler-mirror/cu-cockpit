"""Maintenance-only restore workflow for registered local backup targets."""

import hashlib
import hmac
import json
import os
import re
import secrets
import sqlite3
import stat
import tempfile
import zipfile
from contextlib import ExitStack, closing, contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .backup_center import (MAX_ARCHIVE_BYTES, MAX_CONFIG_BYTES, MAX_CONFIG_TARGETS,
                            MAX_DATABASE_BYTES, _hash_backup_stream, backup_lock,
                            create_backup_archive,
                            read_backup_index, validate_backup_archive, verify_sqlite,
                            write_backup_index)


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


def _validate_restore_database(current: Path, candidate: Path) -> bool:
    if not verify_sqlite(current) or not verify_sqlite(candidate):
        raise ValueError('Restore database is damaged')
    schema = "SELECT type, name, sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' ORDER BY type, name"
    with closing(sqlite3.connect(f'{current.as_uri()}?mode=ro', uri=True)) as original:
        with closing(sqlite3.connect(f'{candidate.as_uri()}?mode=ro', uri=True)) as restored:
            if original.execute(schema).fetchall() != restored.execute(schema).fetchall():
                raise ValueError('Restore database schema differs from installed schema')
            return restored.execute(
                "SELECT count(*) FROM sqlite_master WHERE type='table' AND name='django_session'"
            ).fetchone()[0] == 1


def _clear_restored_sessions(candidate: Path) -> None:
    with closing(sqlite3.connect(candidate)) as database:
        columns = {row[1] for row in database.execute('PRAGMA table_info(django_session)')}
        if not {'session_key', 'session_data', 'expire_date'} <= columns:
            raise ValueError('Invalid Django session schema')
        with database:
            database.execute('DELETE FROM django_session')
    if not verify_sqlite(candidate):
        raise ValueError('Restored database failed integrity check after session cleanup')


@contextmanager
def _stage_restore(root: Path, archive_id: str, targets: dict, version: str,
                   *, clear_sessions: bool = True):
    manifest, _ = _registered_archive(root, archive_id, version)
    if set(manifest['members']) != set(targets):
        raise ValueError('Restore target list differs from archive')
    with ExitStack() as staging:
        staged = {}
        descriptor = os.open(root / f'{archive_id}.zip', os.O_RDONLY | os.O_NOFOLLOW)
        with os.fdopen(descriptor, 'rb') as archive, zipfile.ZipFile(archive) as package:
            for name, target in targets.items():
                original = target.lstat()
                if not stat.S_ISREG(original.st_mode) or original.st_nlink != 1:
                    raise ValueError('Restore target changed type')
                with tempfile.NamedTemporaryFile(dir=target.parent, prefix='.restore-',
                                                 delete=False) as output:
                    temporary = Path(output.name)
                    staging.callback(temporary.unlink, missing_ok=True)
                    os.fchmod(output.fileno(), stat.S_IMODE(original.st_mode))
                    if (os.fstat(output.fileno()).st_uid, os.fstat(output.fileno()).st_gid) != (
                            original.st_uid, original.st_gid):
                        os.fchown(output.fileno(), original.st_uid, original.st_gid)
                    with package.open(name) as source:
                        limit = MAX_DATABASE_BYTES if name == 'app.sqlite3' else MAX_CONFIG_BYTES
                        size, digest = _hash_backup_stream(source, limit, output)
                    if (size != manifest['members'][name]['size'] or
                            not hmac.compare_digest(digest, manifest['members'][name]['sha256'])):
                        raise ValueError('Restore member hash or size mismatch')
                    output.flush()
                    os.fsync(output.fileno())
                staged[name] = temporary
        has_sessions = _validate_restore_database(targets['app.sqlite3'], staged['app.sqlite3'])
        if has_sessions and clear_sessions:
            _clear_restored_sessions(staged['app.sqlite3'])
        yield staged


def _replace_targets(targets: dict, staged: dict, changed: list) -> None:
    configs = {name[len('configs/'):-len('.bin')]: path for name, path in targets.items()
               if name != 'app.sqlite3'}
    for name, target in targets.items():
        _restore_targets(targets['app.sqlite3'], configs)
        temporary = staged[name]
        if temporary.parent != target.parent or not stat.S_ISREG(temporary.lstat().st_mode):
            raise ValueError('Restore staging file is unsafe')
        os.replace(temporary, target)
        changed.append(name)
        descriptor = os.open(target.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)


def _check_restore_task(root: Path, task_id: str, targets: dict, version: str) -> dict:
    if not isinstance(task_id, str) or not re.fullmatch(r'[0-9a-f]{32}', task_id):
        raise ValueError('Invalid restore task ID')
    task = read_backup_index(root)['tasks'].get(task_id)
    if (not isinstance(task, dict) or task.get('kind') != 'restore' or
            task.get('status') != 'awaiting_maintenance' or task.get('version') != version or
            task.get('targets') != {name: str(path) for name, path in targets.items()} or
            datetime.fromisoformat(task['expires_at']) <= datetime.now(timezone.utc)):
        raise ValueError('Restore task is not eligible for maintenance')
    if task['services'] != _restore_services(task['services']):
        raise ValueError('Restore service registry has changed')
    manifest, digest = _registered_archive(root, task['archive_id'], version)
    if digest != task['archive_hash'] or set(manifest['members']) != set(targets):
        raise ValueError('Confirmed restore archive or targets have changed')
    return task


def _set_restore_state(root: Path, task_id: str, status: str, **details) -> None:
    index = read_backup_index(root)
    index['tasks'][task_id].update(status=status, **details)
    write_backup_index(root, index, locked=True)


def _checkpoint_restore_database(db_path: Path) -> None:
    with closing(sqlite3.connect(db_path)) as database:
        if database.execute('PRAGMA wal_checkpoint(TRUNCATE)').fetchone()[0]:
            raise RuntimeError('Restore database has active WAL writers')


def _rollback_restore_targets(targets: dict, safety_staged: dict, changed: list) -> None:
    for name in reversed(changed):
        target = targets[name]
        os.replace(safety_staged[name], target)
        descriptor = os.open(target.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    if 'app.sqlite3' in changed and not verify_sqlite(targets['app.sqlite3']):
        raise RuntimeError('Rolled back database failed integrity check')


def _apply_confirmed_restore(root: Path, task: dict, targets: dict, version: str,
                             controller, active: list) -> str:
    configs = {name[len('configs/'):-len('.bin')]: path for name, path in targets.items()
               if name != 'app.sqlite3'}
    safety = create_backup_archive(root, targets['app.sqlite3'], configs, version,
                                   f"restore-safety:{task['actor']}", locked=True)
    safety_id = safety['archive_id']
    _set_restore_state(root, task['id'], 'running', safety_archive_id=safety_id)
    changed = []
    with _stage_restore(root, safety_id, targets, version, clear_sessions=False) as rollback:
        try:
            with _stage_restore(root, task['archive_id'], targets, version) as staged:
                _replace_targets(targets, staged, changed)
                if not verify_sqlite(targets['app.sqlite3']):
                    raise RuntimeError('Restored database failed integrity check')
            _resume_services(controller, active)
            _set_restore_state(root, task['id'], 'completed',
                               completed_at=datetime.now(timezone.utc).isoformat())
        except Exception as error:
            try:
                if changed:
                    if any(controller.is_active(service) for service in task['services']):
                        _pause_services(controller, task['services'])
                    _rollback_restore_targets(targets, rollback, changed)
            except Exception as rollback_error:
                raise RuntimeError(
                    f'Restore failed; manual rollback from {safety_id} required: '
                    f'{rollback_error}') from error
            raise
    return safety_id


def restore_confirmed(root: Path, task_id: str, db_path: Path, configs: dict,
                      version: str, controller) -> dict:
    targets = {name: Path(path) for name, path in _restore_targets(db_path, configs).items()}
    with backup_lock(root):
        task = _check_restore_task(root, task_id, targets, version)
        _set_restore_state(root, task_id, 'running')
        active = []
        try:
            active = _pause_services(controller, task['services'])
            _checkpoint_restore_database(db_path)
            safety_id = _apply_confirmed_restore(root, task, targets, version, controller, active)
            return {'id': task_id, 'status': 'completed', 'safety_archive_id': safety_id}
        except Exception as error:
            message = str(error)
            try:
                _resume_services(controller, active)
            except Exception as restart_error:
                message = f'{message}; {restart_error}'
            _set_restore_state(root, task_id, 'failed', error=message)
            return {'id': task_id, 'status': 'failed', 'error': message}