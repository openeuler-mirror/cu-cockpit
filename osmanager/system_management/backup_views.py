"""Administrator-only HTTP facade for local backup jobs."""

import hashlib
import hmac
import json
import os
import re
import stat
import zipfile
from contextlib import ExitStack

from django.http import FileResponse, JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST

from .backup_center import read_backup_index
from .backup_jobs import queue_backup, read_backup_schedule
from .backup_restore import _registered_archive
from .backup_runtime import (BACKUP_COMPAT_VERSION, backup_configs, backup_database,
                             require_installation)
from .permissions import admin_required_api, audited_admin_api, get_session_identity


def _error(code, message):
    return JsonResponse({'code': code, 'message': message}, status=code)


def _archive_id(value):
    if not isinstance(value, str) or not re.fullmatch(r'[0-9a-f]{32}', value):
        raise ValueError('Invalid archive ID')
    return value


def _payload(request):
    if (request.content_type != 'application/json' or
            len(request.body) > 4096):
        raise ValueError('Bounded application/json body required')
    value = json.loads(request.body, parse_constant=lambda value: (_ for _ in ()).throw(
        ValueError('Non-JSON numeric constant')))
    if not isinstance(value, dict):
        raise ValueError('JSON object required')
    return value


def _verify_request(request):
    payload = _payload(request)
    if set(payload) != {'archive_id'}:
        raise ValueError('Expected only archive_id')
    return _archive_id(payload['archive_id'])


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
    try:
        can_create = backup_database().is_file() and bool(backup_configs())
    except (OSError, ValueError):
        can_create = False
    return JsonResponse({
        'available': True, 'backups': backups, 'tasks': tasks,
        'schedule': {key: schedule[key] for key in (
            'enabled', 'time', 'timezone', 'next_run')},
        'capabilities': {'create': can_create, 'verify': True, 'schedule': True,
                         'create_reason': None if can_create else
                         'Backup database or registered configuration is unavailable'},
    })


@audited_admin_api('backup', 'create')
@require_POST
def backup_create(request):
    try:
        if _payload(request):
            raise ValueError('Backup creation accepts no client options')
    except (ValueError, UnicodeDecodeError):
        return _error(400, 'Expected an empty JSON object')
    try:
        root = require_installation()
    except (OSError, ValueError):
        return _error(503, 'Backup installation is unavailable')
    try:
        task = queue_backup(root, get_session_identity(request).username)
    except BlockingIOError:
        return _error(409, 'Backup service is busy')
    except ValueError as error:
        if str(error) == 'Backup task history is full':
            return _error(409, 'Backup task history is full')
        return _error(503, 'Backup task index is unavailable')
    except OSError:
        return _error(503, 'Backup queue storage is unavailable')
    return JsonResponse({'task': {key: task[key] for key in (
        'id', 'kind', 'status', 'created_at')}}, status=202)


@audited_admin_api('backup', 'verify')
@require_POST
def backup_verify(request):
    try:
        archive_id = _verify_request(request)
    except (ValueError, UnicodeDecodeError):
        return _error(400, 'Expected only a valid archive_id')
    try:
        root = require_installation()
    except (OSError, ValueError):
        return _error(503, 'Backup installation is unavailable')
    try:
        manifest, _ = _registered_archive(root, archive_id, BACKUP_COMPAT_VERSION)
    except (ValueError, KeyError, zipfile.BadZipFile):
        return _error(422, 'Archive is not registered or failed verification')
    except OSError:
        return _error(503, 'Backup archive storage is unavailable')
    return JsonResponse({'archive_id': archive_id, 'members': sorted(manifest['members']),
                         'total_size': sum(member['size'] for member in
                                           manifest['members'].values())})


@audited_admin_api('backup', 'download')
@require_GET
def backup_download(request, archive_id):
    try:
        if request.GET:
            raise ValueError('Download does not accept query parameters')
        _archive_id(archive_id)
    except ValueError:
        return _error(400, 'Expected only a valid archive_id')
    root = require_installation()
    _, expected_hash = _registered_archive(root, archive_id, BACKUP_COMPAT_VERSION)
    descriptor = os.open(root / f'{archive_id}.zip', os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with ExitStack() as opened:
        archive = opened.enter_context(os.fdopen(descriptor, 'rb'))
        details = os.fstat(archive.fileno())
        if not stat.S_ISREG(details.st_mode) or details.st_nlink != 1:
            raise ValueError('Archive file is not a standalone regular file')
        if not hmac.compare_digest(hashlib.file_digest(archive, 'sha256').hexdigest(),
                                   expected_hash):
            raise ValueError('Archive file changed after verification')
        archive.seek(0)
        response = FileResponse(archive, as_attachment=True, filename=f'{archive_id}.zip')
        response['Cache-Control'] = 'private, no-store'
        opened.pop_all()
        return response