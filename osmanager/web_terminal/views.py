import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from osmanager.auth.decorators import login_required_api
from django.views.decorators.csrf import ensure_csrf_cookie
from django.middleware.csrf import get_token

WEBSSH_URL = "http://127.0.0.1:8001"


@login_required_api
def auth_check(request):
    # 通过自有的登录校验，返回200
    return JsonResponse({"ok": True}, status=200)

@login_required_api
def terminal_connect(request):
    data = request.POST.dict()
    real_ip = request.META.get('HTTP_X_REAL_IP') or request.META.get('REMOTE_ADDR', '')
    xff = request.META.get('HTTP_X_FORWARDED_FOR', '')
    headers = {
        'X-Real-IP': real_ip,
        'X-Forwarded-For': (xff + ', ' if xff else '') + real_ip,
    }

    s = requests.Session()
    # 1) 先 GET 一次，让 webssh 发 _xsrf cookie
    s.get(WEBSSH_URL + '/', timeout=5)
    token = s.cookies.get('_xsrf')
    if token:
        data['_xsrf'] = token

    # 2) 带着 cookie 和 _xsrf 发 POST /
    resp = s.post(WEBSSH_URL + '/', data=data, headers=headers, timeout=10)

    return JsonResponse(resp.json(), status=resp.status_code)

@login_required_api
@ensure_csrf_cookie
def csrf_token(request):
    return JsonResponse({'csrftoken': get_token(request)})

