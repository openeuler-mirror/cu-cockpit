"""Persistent backup jobs and daily scheduling."""

import hashlib
import json
import os
import re
import secrets
import stat
import tempfile
from contextlib import nullcontext
from datetime import datetime, time as clock_time, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .backup_center import (backup_lock, create_backup_archive, read_backup_index,
                            validate_backup_root, write_backup_index)


def queue_backup(root, actor):
    if not isinstance(actor, str) or not actor or len(actor) > 128:
        raise ValueError('Invalid backup actor')
    with backup_lock(root):
        index = read_backup_index(root) if os.path.lexists(root / 'index.json') else {
            'tasks': {}, 'backups': {}}
        if len(index['tasks']) >= 256:
            completed = next((task_id for task_id, task in index['tasks'].items()
                              if task.get('kind', 'backup') == 'backup' and
                              task['status'] in ('succeeded', 'failed')), None)
            if completed is None:
                raise ValueError('Backup task history is full')
            del index['tasks'][completed]
        task_id = secrets.token_hex(16)
        task = {'id': task_id, 'kind': 'backup', 'actor': actor, 'status': 'queued',
                'created_at': datetime.now(timezone.utc).isoformat()}
        index['tasks'][task_id] = task
        write_backup_index(root, index, locked=True)
        return task.copy()


def get_backup_task(root, task_id):
    if not isinstance(task_id, str) or not re.fullmatch(r'[0-9a-f]{32}', task_id):
        raise ValueError('Invalid backup task ID')
    index = read_backup_index(root) if os.path.lexists(root / 'index.json') else {
        'tasks': {}, 'backups': {}}
    return index['tasks'].get(task_id)


def list_backup_tasks(root):
    index = read_backup_index(root) if os.path.lexists(root / 'index.json') else {
        'tasks': {}, 'backups': {}}
    return sorted((task for task in index['tasks'].values()
                   if task.get('kind', 'backup') == 'backup'),
                  key=lambda task: task['created_at'], reverse=True)


def run_pending(root, db_path, configs, version):
    with backup_lock(root):
        index = read_backup_index(root) if os.path.lexists(root / 'index.json') else {
            'tasks': {}, 'backups': {}}
        interrupted = [task for task in index['tasks'].values()
                   if task.get('kind', 'backup') == 'backup' and task['status'] == 'running']
        for task in interrupted:
            task['status'] = 'failed'
            task['error'] = 'Backup worker interrupted'
            task['finished_at'] = datetime.now(timezone.utc).isoformat()
        if interrupted:
            write_backup_index(root, index, locked=True)
        queued = sorted((task for task in index['tasks'].values()
                         if task.get('kind', 'backup') == 'backup' and
                         task['status'] == 'queued'), key=lambda task: task['created_at'])
        if not queued:
            return None
        task = queued[0]
        task['status'] = 'running'
        task['started_at'] = datetime.now(timezone.utc).isoformat()
        write_backup_index(root, index, locked=True)
        try:
            record = create_backup_archive(root, db_path, configs, version,
                                           task['actor'], locked=True)
        except Exception:
            index = read_backup_index(root)
            task = index['tasks'][task['id']]
            task['status'] = 'failed'
            task['error'] = 'Backup operation failed'
            task['finished_at'] = datetime.now(timezone.utc).isoformat()
            write_backup_index(root, index, locked=True)
            return task.copy()
        index = read_backup_index(root)
        task = index['tasks'][task['id']]
        task['status'] = 'succeeded'
        task['archive_id'] = record['archive_id']
        task['result'] = record
        task['finished_at'] = datetime.now(timezone.utc).isoformat()
        write_backup_index(root, index, locked=True)
        return task.copy()


def _validate_schedule(schedule):
    if not isinstance(schedule, dict) or set(schedule) != {
            'enabled', 'time', 'timezone', 'last_slot'}:
        raise ValueError('Invalid backup schedule fields')
    if type(schedule['enabled']) is not bool or not isinstance(schedule['time'], str) or not re.fullmatch(
            r'(?:[01][0-9]|2[0-3]):[0-5][0-9]', schedule['time']):
        raise ValueError('Invalid backup schedule settings')
    if not isinstance(schedule['timezone'], str) or len(schedule['timezone']) > 128:
        raise ValueError('Invalid backup schedule timezone')
    try:
        ZoneInfo(schedule['timezone'])
    except (ZoneInfoNotFoundError, ValueError) as error:
        raise ValueError('Invalid backup schedule timezone') from error
    slot = schedule['last_slot']
    if slot is not None and (not isinstance(slot, str) or not re.fullmatch(
            r'\d{4}-\d{2}-\d{2}', slot)):
        raise ValueError('Invalid backup schedule slot')
    if slot is not None:
        try:
            datetime.strptime(slot, '%Y-%m-%d')
        except ValueError as error:
            raise ValueError('Invalid backup schedule slot') from error


def read_backup_schedule(root, now=None):
    validate_backup_root(root)
    if not os.path.lexists(root / 'schedule.json'):
        return {'enabled': False, 'time': '02:00', 'timezone': 'UTC',
                'last_slot': None, 'next_run': None}
    descriptor = os.open(root / 'schedule.json', os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, 'r', encoding='utf-8') as schedule_file:
        details = os.fstat(schedule_file.fileno())
        if not stat.S_ISREG(details.st_mode) or details.st_mode & 0o077:
            raise PermissionError('Backup schedule must be a private regular file')
        if details.st_size > 4096:
            raise ValueError('Backup schedule exceeds size limit')
        schedule = json.load(schedule_file)
    _validate_schedule(schedule)
    next_run = None
    if schedule['enabled']:
        zone = ZoneInfo(schedule['timezone'])
        instant = now if now is not None else datetime.now(timezone.utc)
        if not isinstance(instant, datetime) or instant.tzinfo is None or (
                instant.utcoffset() is None):
            raise ValueError('Backup schedule requires an aware datetime')
        local = instant.astimezone(zone)
        day = local.date()
        if schedule['last_slot'] == day.isoformat() or local.strftime('%H:%M') >= schedule['time']:
            day += timedelta(days=1)
        next_run = datetime.combine(day, clock_time.fromisoformat(schedule['time']),
                                    tzinfo=zone).isoformat()
    return {**schedule, 'next_run': next_run}


def write_backup_schedule(root, schedule, *, locked=False):
    _validate_schedule(schedule)
    payload = json.dumps(schedule, allow_nan=False).encode('utf-8')
    with nullcontext() if locked else backup_lock(root):
        if os.path.lexists(root / 'schedule.json'):
            read_backup_schedule(root)
        with tempfile.TemporaryDirectory(dir=root, prefix='.schedule-') as staging:
            temporary = Path(staging) / 'schedule.json'
            descriptor = os.open(temporary, os.O_CREAT | os.O_EXCL | os.O_WRONLY |
                                 os.O_NOFOLLOW, 0o600)
            with os.fdopen(descriptor, 'wb') as schedule_file:
                schedule_file.write(payload)
                schedule_file.flush()
                os.fsync(schedule_file.fileno())
            os.replace(temporary, root / 'schedule.json')
            directory_fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)


def save_backup_schedule(root, enabled, time, timezone_name='UTC'):
    with backup_lock(root):
        previous = read_backup_schedule(root)
        schedule = {'enabled': enabled, 'time': time, 'timezone': timezone_name,
                    'last_slot': previous['last_slot']}
        write_backup_schedule(root, schedule, locked=True)
        return read_backup_schedule(root)


def queue_due_backup(root, now=None):
    with backup_lock(root):
        schedule = read_backup_schedule(root)
        if not schedule['enabled']:
            return None
        instant = now if now is not None else datetime.now(timezone.utc)
        if not isinstance(instant, datetime) or instant.tzinfo is None or (
                instant.utcoffset() is None):
            raise ValueError('Backup schedule requires an aware datetime')
        local = instant.astimezone(ZoneInfo(schedule['timezone']))
        slot = local.date().isoformat()
        if schedule['last_slot'] == slot or local.strftime('%H:%M') < schedule['time']:
            return None
        task_id = hashlib.sha256(f'daily:{slot}'.encode('ascii')).hexdigest()[:32]
        index = read_backup_index(root) if os.path.lexists(root / 'index.json') else {
            'tasks': {}, 'backups': {}}
        if task_id not in index['tasks']:
            if len(index['tasks']) >= 256:
                completed = next((key for key, task in index['tasks'].items()
                                  if task.get('kind', 'backup') == 'backup' and
                                  task['status'] in ('succeeded', 'failed')), None)
                if completed is None:
                    raise ValueError('Backup task history is full')
                del index['tasks'][completed]
            task = {'id': task_id, 'kind': 'backup', 'actor': 'daily-schedule', 'status': 'queued',
                    'created_at': instant.astimezone(timezone.utc).isoformat()}
            index['tasks'][task_id] = task
            write_backup_index(root, index, locked=True)
        schedule.pop('next_run')
        schedule['last_slot'] = slot
        write_backup_schedule(root, schedule, locked=True)
        return index['tasks'][task_id].copy()