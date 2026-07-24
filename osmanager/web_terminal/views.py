import ipaddress
import os
import re

import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from osmanager.auth.decorators import login_required_api
from django.views.decorators.csrf import ensure_csrf_cookie
from django.middleware.csrf import get_token
from osmanager.system_management.permissions import audited_admin_api

WEBSSH_URL = os.environ.get('WEBSSH_URL', 'http://127.0.0.1:8002').rstrip('/')
HOST_LABEL_PATTERN = re.compile(r'^[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?$')
USERNAME_PATTERN = re.compile(r'^[A-Za-z0-9_.@-]{1,64}$')
PRIVATE_KEY_LIMIT = 128 * 1024


def _valid_hostname(value):
    try:
        ipaddress.ip_address(value)
        return True
    except ValueError:
        labels = value.rstrip('.').split('.')
        return bool(labels) and len(value) <= 253 and all(HOST_LABEL_PATTERN.fullmatch(label) for label in labels)


def _connection_data(request):
    raw = request.POST.dict()
    hostname = str(raw.get('hostname') or raw.get('host') or '').strip()
    username = str(raw.get('username', '')).strip()
    password = str(raw.get('password', ''))
    privatekey = str(raw.get('privatekey', ''))
    passphrase = str(raw.get('passphrase', ''))
    term = str(raw.get('term', 'xterm-256color')).strip()
    try:
        port = int(raw.get('port', 22))
    except (TypeError, ValueError) as error:
        raise ValueError('SSH 端口必须为整数') from error
    if not _valid_hostname(hostname):
        raise ValueError('目标主机名或 IP 不合法')
    if not 1 <= port <= 65535:
        raise ValueError('SSH 端口范围必须为 1-65535')
    if not USERNAME_PATTERN.fullmatch(username):
        raise ValueError('SSH 用户名格式不合法')
    if bool(password) == bool(privatekey):
        raise ValueError('密码和私钥必须且只能提供一种')
    if len(password) > 4096 or len(passphrase) > 4096:
        raise ValueError('认证字段超过长度限制')
    if privatekey:
        if len(privatekey.encode('utf-8')) > PRIVATE_KEY_LIMIT:
            raise ValueError('私钥超过大小限制')
        first_line = privatekey.lstrip().splitlines()[0] if privatekey.strip() else ''
        if not first_line.startswith('-----BEGIN ') or 'PRIVATE KEY-----' not in first_line:
            raise ValueError('私钥格式不合法')
    if term not in ('xterm', 'xterm-256color', 'vt100', 'linux'):
        raise ValueError('终端类型不支持')
    return {
        'hostname': hostname,
        'port': str(port),
        'username': username,
        'password': password,
        'privatekey': privatekey,
        'passphrase': passphrase,
        'term': term,
    }


@login_required_api
def auth_check(request):
    # 通过自有的登录校验，返回200
    return JsonResponse({"ok": True}, status=200)

@audited_admin_api('terminal', 'connect')
def terminal_connect(request):
    if request.method != 'POST':
        return JsonResponse({'code': 405, 'message': '仅支持 POST'}, status=405,
                            json_dumps_params={'ensure_ascii': False})
    try:
        data = _connection_data(request)
    except ValueError as error:
        return JsonResponse({'code': 400, 'message': str(error)}, status=400,
                            json_dumps_params={'ensure_ascii': False})
    real_ip = request.META.get('HTTP_X_REAL_IP') or request.META.get('REMOTE_ADDR', '')
    xff = request.META.get('HTTP_X_FORWARDED_FOR', '')
    headers = {
        'X-Real-IP': real_ip,
        'X-Forwarded-For': (xff + ', ' if xff else '') + real_ip,
        'Origin': request.META.get('HTTP_ORIGIN') or f'{request.scheme}://{request.get_host()}',
    }

    s = requests.Session()
    # 1) 先 GET 一次，让 webssh 发 _xsrf cookie
    s.get(WEBSSH_URL + '/', timeout=5)
    token = s.cookies.get('_xsrf')
    if token:
        data['_xsrf'] = token

    # 2) 带着 cookie 和 _xsrf 发 POST /
    resp = s.post(WEBSSH_URL + '/', data=data, headers=headers, timeout=15)

    try:
        payload = resp.json()
    except ValueError:
        return JsonResponse({'code': 502, 'message': 'WebSSH 返回无效响应'}, status=502,
                            json_dumps_params={'ensure_ascii': False})
    return JsonResponse(payload, status=resp.status_code)

@login_required_api
@ensure_csrf_cookie
def csrf_token(request):
    return JsonResponse({'csrftoken': get_token(request)})

