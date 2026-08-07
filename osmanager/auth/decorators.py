# osmanager/osmanager/auth/decorators.py

from django.http import JsonResponse
from functools import wraps
from rest_framework.permissions import BasePermission


class HasSystemSession(BasePermission):
    def has_permission(self, request, view):
        return bool(getattr(request, 'session', {}).get('username'))

def login_required_api(view_func):
    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        if 'username' not in request.session:
            return JsonResponse({'code': 401, 'message': '未登录，禁止访问'}, status=401, json_dumps_params={'ensure_ascii': False})
        return view_func(request, *args, **kwargs)
    return wrapped_view
