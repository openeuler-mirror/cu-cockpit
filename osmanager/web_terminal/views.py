import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from osmanager.auth.decorators import login_required_api
from django.views.decorators.csrf import ensure_csrf_cookie
from django.middleware.csrf import get_token
WEBSSH_URL = 'http://127.0.0.1:8001'

@login_required_api
def auth_check(request):
    return JsonResponse({'ok': True}, status=200)

@login_required_api
def terminal_connect(request):
    data = request.POST.dict()
    real_ip = request.META.get('HTTP_X_REAL_IP') or request.META.get('REMOTE_ADDR', '')
    xff = request.META.get('HTTP_X_FORWARDED_FOR', '')
    headers = {'X-Real-IP': real_ip, 'X-Forwarded-For': (xff + ', ' if xff else '') + real_ip}
    s = requests.Session()
    s.get(WEBSSH_URL + '/', timeout=5)
    token = s.cookies.get('_xsrf')
    pass

@login_required_api
@ensure_csrf_cookie
def csrf_token(request):
    pass
