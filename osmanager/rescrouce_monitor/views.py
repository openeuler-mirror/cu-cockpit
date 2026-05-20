import subprocess
import json
import os
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from osmanager.auth.decorators import login_required_api
ALLOWED_SCRIPT_MODES = {'monitor_status.sh': ['all', 'cpu', 'disk', 'memory', 'network'], 'hard_info.sh': ['cpu', 'disk', 'network', 'system', 'bios', 'os_system', 'storage'], 'memory_slot.sh': [], 'pci_info.sh': []}
ALLOWED_SCRIPTS = list(ALLOWED_SCRIPT_MODES.keys())

@swagger_auto_schema(method='get', manual_parameters=[openapi.Parameter('script_name', openapi.IN_PATH, type=openapi.TYPE_STRING, description='脚本名', enum=ALLOWED_SCRIPTS), openapi.Parameter('mode', openapi.IN_QUERY, type=openapi.TYPE_STRING, description="不同脚本可选值不同：monitor_status.sh -> ['all','cpu','disk','memory','network']；hard_info.sh -> ['cpu','disk','network','system','bios','os_system','storage']", enum=sorted({m for v in ALLOWED_SCRIPT_MODES.values() for m in v}))], responses={200: openapi.Response(description='执行成功'), 404: openapi.Response(description='脚本未找到'), 400: openapi.Response(description='传参错误'), 500: openapi.Response(description='脚本执行失败'), 408: openapi.Response(description='超时'), 501: openapi.Response(description='调用脚本执行失败'), 502: openapi.Response(description='位置错误')})
@login_required_api
@api_view(['GET'])
def run_shell_script_api(request, script_name):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    SCRIPTS_DIR = os.path.join(current_dir, 'manager-script')
    script_path = os.path.join(SCRIPTS_DIR, script_name)
    if not os.path.isfile(script_path):
        return Response({'error': 'not found manager_script', 'script': script_name, 'script_path': script_path}, status=404)
    pass
