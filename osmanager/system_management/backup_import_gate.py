"""Reject unauthorized or unbounded backup uploads before CSRF parses multipart data."""

from django.http import JsonResponse

from .audit import record_audit
from .backup_center import MAX_ARCHIVE_BYTES
from .permissions import get_session_identity


class BackupImportGate:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method != 'POST' or request.path_info != '/api/system/backups/import':
            return self.get_response(request)

        identity = get_session_identity(request)
        if not identity.username:
            return JsonResponse({'code': 401, 'message': '未登录，禁止访问'}, status=401)
        if not identity.is_admin:
            record_audit(request, 'system', 'permission_denied', request.path,
                         message='需要管理员权限', detail={'method': request.method})
            return JsonResponse({'code': 403, 'message': '需要管理员权限'}, status=403)

        length = request.META.get('CONTENT_LENGTH', '')
        maximum = MAX_ARCHIVE_BYTES + 1024 * 1024
        if (not length.isascii() or not length.isdecimal() or
                len(length) > len(str(maximum)) or int(length) > maximum or
                request.content_type != 'multipart/form-data'):
            return JsonResponse({'code': 400, 'message': 'Bounded multipart upload required'},
                                status=400)
        return self.get_response(request)
