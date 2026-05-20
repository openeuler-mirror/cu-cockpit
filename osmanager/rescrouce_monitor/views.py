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
    try:
        script_args = ['bash', script_path]
        mode = request.GET.get('mode')
        if script_name == 'monitor_status.sh':
            allowed_modes = ['all', 'cpu', 'disk', 'memory', 'network']
        elif script_name == 'hard_info.sh':
            allowed_modes = ['cpu', 'disk', 'network', 'system', 'bios', 'os_system', 'storage']
        if script_name in ['monitor_status.sh', 'hard_info.sh']:
            if mode is None or not str(mode).strip():
                return JsonResponse({'error': '参数错误', 'message': 'mode 必填且不能为空'}, status=400)
            if mode not in allowed_modes:
                return JsonResponse({'error': '参数错误', 'message': f'mode 只允许为 {allowed_modes}，你传入的是: {mode}'}, status=400)
            script_args.append(mode)
        elif mode is not None:
            return JsonResponse({'error': '参数错误', 'message': '该脚本不支持 mode 参数'}, status=400)
        try:
            result = subprocess.run(script_args, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            return_code = result.returncode
            stdout = result.stdout.strip()
            stderr = result.stderr.strip()
            if return_code != 0 or stderr:
                return JsonResponse({'error': '脚本执行失败', 'script': script_name, 'return_code': return_code, 'stdout': stdout if stdout else None, 'stderr': stderr if stderr else None}, status=500, json_dumps_params={'ensure_ascii': False})
            else:
                try:
                    json_data = json.loads(stdout)
                    return JsonResponse(json_data, safe=False, json_dumps_params={'ensure_ascii': False})
                except json.JSONDecodeError:
                    return JsonResponse({'message': 'success,but not json', 'output': stdout})
        except subprocess.TimeoutExpired as e:
            return JsonResponse({'error': '脚本执行超时', 'script': script_name, 'details': str(e)}, status=408, json_dumps_params={'ensure_ascii': False})
        except FileNotFoundError as e:
            return JsonResponse({'error': '脚本文件未找到或bash命令不存在', 'script': script_name, 'details': str(e)}, status=404, json_dumps_params={'ensure_ascii': False})
        except Exception as e:
            return JsonResponse({'error': '脚本执行异常', 'script': script_name, 'details': str(e)}, status=500, json_dumps_params={'ensure_ascii': False})
    except subprocess.CalledProcessError as e:
        return JsonResponse({'error': '调用脚本执行失败', 'script': script_name, 'stderr': e.stderr.strip()}, status=500, json_dumps_params={'ensure_ascii': False})
    except Exception as e:
        return JsonResponse({'error': '未知错误', 'details': str(e), 'script': script_name}, status=500, json_dumps_params={'ensure_ascii': False})
