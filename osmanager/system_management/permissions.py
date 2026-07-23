import pwd
from dataclasses import asdict, dataclass
from functools import wraps

from django.http import JsonResponse

from .audit import record_audit


@dataclass(frozen=True)
class SessionIdentity:
    username: str
    role: str
    uid: int | None

    @property
    def is_admin(self):
        return self.role == 'admin'

    def to_dict(self):
        data = asdict(self)
        data['is_admin'] = self.is_admin
        data['permissions'] = ['read', 'write', 'audit', 'rollback'] if self.is_admin else ['read']
        return data


def get_session_identity(request):
    username = request.session.get('username', '') if hasattr(request, 'session') else ''
    if not username:
        return SessionIdentity(username='', role='anonymous', uid=None)
    try:
        uid = pwd.getpwnam(username).pw_uid
    except KeyError:
        return SessionIdentity(username=username, role='viewer', uid=None)
    return SessionIdentity(username=username, role='admin' if uid == 0 else 'viewer', uid=uid)


def admin_required_api(view_func):
    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        identity = get_session_identity(request)
        if not identity.username:
            return JsonResponse({'code': 401, 'message': '未登录，禁止访问'}, status=401,
                                json_dumps_params={'ensure_ascii': False})
        if not identity.is_admin:
            record_audit(
                request,
                module='system',
                action='permission_denied',
                target=request.path,
                success=False,
                message='需要管理员权限',
                detail={'method': request.method},
            )
            return JsonResponse({'code': 403, 'message': '需要管理员权限'}, status=403,
                                json_dumps_params={'ensure_ascii': False})
        request.system_identity = identity
        return view_func(request, *args, **kwargs)

    return wrapped_view


def audited_admin_api(module, action):
    def decorator(view_func):
        protected_view = admin_required_api(view_func)

        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            identity = get_session_identity(request)
            try:
                response = protected_view(request, *args, **kwargs)
            except Exception as error:
                if identity.is_admin:
                    record_audit(request, module, action, request.path, False, str(error),
                                 {'method': request.method})
                raise
            if identity.is_admin:
                status_code = getattr(response, 'status_code', 500)
                record_audit(
                    request,
                    module=module,
                    action=action,
                    target=request.path,
                    success=status_code < 400,
                    message=f'HTTP {status_code}',
                    detail={'method': request.method, 'status_code': status_code},
                )
            return response

        return wrapped_view

    return decorator