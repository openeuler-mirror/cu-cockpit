"""Persistent backup jobs and daily scheduling."""

import os
import re
import secrets
from datetime import datetime, timezone

from .backup_center import backup_lock, read_backup_index, write_backup_index


def queue_backup(root, actor):
    if not isinstance(actor, str) or not actor or len(actor) > 128:
        raise ValueError('Invalid backup actor')
    with backup_lock(root):
        index = read_backup_index(root) if os.path.lexists(root / 'index.json') else {
            'tasks': {}, 'backups': {}}
        if len(index['tasks']) >= 256:
            raise ValueError('Backup task history is full')
        task_id = secrets.token_hex(16)
        task = {'id': task_id, 'actor': actor, 'status': 'queued',
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
    return sorted(index['tasks'].values(), key=lambda task: task['created_at'], reverse=True)