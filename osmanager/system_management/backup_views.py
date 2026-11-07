"""Administrator-only HTTP facade for local backup jobs."""

import json
import os

from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET

from .backup_center import read_backup_index
from .backup_jobs import read_backup_schedule
from .backup_runtime import backup_configs, backup_database, require_installation
from .permissions import admin_required_api


def _error(code, message):
    return JsonResponse({'code': code, 'message': message}, status=code)


def _payload(request):
    if (request.content_type != 'application/json' or
            len(request.body) > 4096):
        raise ValueError('Bounded application/json body required')
    value = json.loads(request.body, parse_constant=lambda value: (_ for _ in ()).throw(
        ValueError('Non-JSON numeric constant')))
    if not isinstance(value, dict):
        raise ValueError('JSON object required')
    return value


@admin_required_api
@ensure_csrf_cookie
@require_GET
def backup_overview(request):
    try:
        root = require_installation()
    except FileNotFoundError:
        return JsonResponse({'available': False, 'reason': 'Backup installation is not initialized',
                             'capabilities': {'create': False, 'verify': False, 'schedule': False}},
                            status=503)
    except (OSError, ValueError):
        return JsonResponse({'available': False, 'reason': 'Backup installation is invalid or inaccessible',
                             'capabilities': {'create': False, 'verify': False, 'schedule': False}},
                            status=503)
    index = read_backup_index(root) if os.path.lexists(root / 'index.json') else {
        'backups': {}, 'tasks': {}}
    backups = [{key: record[key] for key in (
        'archive_id', 'application_version', 'actor', 'size') if key in record}
        for record in index['backups'].values()]
    tasks = [{key: task[key] for key in (
        'id', 'kind', 'status', 'created_at', 'started_at', 'finished_at', 'archive_id')
        if key in task} for task in index['tasks'].values()
        if task.get('kind', 'backup') == 'backup']
    schedule = read_backup_schedule(root)
    return JsonResponse({
        'available': True, 'backups': backups, 'tasks': tasks,
        'schedule': {key: schedule[key] for key in (
            'enabled', 'time', 'timezone', 'next_run')},
        'capabilities': {'create': backup_database().is_file() and bool(backup_configs()),
                         'verify': True, 'schedule': True},
    })