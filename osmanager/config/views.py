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
from rest_framework.parsers import BaseParser
from pathlib import Path
from rest_framework.decorators import api_view, parser_classes
from django.http import HttpResponse
from osmanager.auth.decorators import login_required_api

class AnyBinaryParser(BaseParser):
    media_type = '*/*'

    def parse(self, stream, media_type=None, parser_context=None):
        return stream.read()
ALLOWED_SCRIPT_MODES = {'config.sh': ['sshkey', 'gethostname', 'time', 'get']}
SCRIPT_OUTPUT_FORMATS = {'sshkey': 'json', 'gethostname': 'text', 'time': 'json', 'get': 'text'}
ALLOWED_SCRIPTS = list(ALLOWED_SCRIPT_MODES.keys())

@swagger_auto_schema(method='get', manual_parameters=[openapi.Parameter('script_name', openapi.IN_PATH, type=openapi.TYPE_STRING, description='脚本名', enum=ALLOWED_SCRIPTS), openapi.Parameter('mode', openapi.IN_QUERY, type=openapi.TYPE_STRING, description="参数：config.sh -> ['sshkey','gethostname','time','get']", enum=sorted({m for v in ALLOWED_SCRIPT_MODES.values() for m in v})), openapi.Parameter('key', openapi.IN_QUERY, description='当 mode=get 时必填；例如：/?mode=get&key=bashrc', type=openapi.TYPE_STRING, required=False)], responses={200: openapi.Response(description='执行成功'), 404: openapi.Response(description='脚本未找到'), 400: openapi.Response(description='传参错误'), 500: openapi.Response(description='脚本执行失败'), 408: openapi.Response(description='超时'), 501: openapi.Response(description='调用脚本执行失败'), 502: openapi.Response(description='位置错误')})
@login_required_api
@api_view(['GET'])
def get_config_api(request, script_name):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    SCRIPTS_DIR = os.path.join(current_dir, 'manager-script')
    script_path = os.path.join(SCRIPTS_DIR, script_name)
    if not os.path.isfile(script_path):
        return Response({'error': 'not found manager_script', 'script': script_name, 'script_path': script_path}, status=404)
    try:
        script_extension = os.path.splitext(script_name)[1].lower()
        if script_extension == '.py':
            script_args = ['python3', script_path]
        elif script_extension == '.sh':
            script_args = ['bash', script_path]
        else:
            script_args = ['bash', script_path]
        mode = request.GET.get('mode')
        allowed_modes = ALLOWED_SCRIPT_MODES['config.sh']
        if mode is None or not str(mode).strip():
            return JsonResponse({'error': '参数错误', 'message': 'mode 必填且不能为空'}, status=400, json_dumps_params={'ensure_ascii': False})
        if mode not in allowed_modes:
            return JsonResponse({'error': '参数错误', 'message': f'mode 只允许为 {allowed_modes}，你传入的是: {mode}'}, status=400, json_dumps_params={'ensure_ascii': False})
        if mode == 'get':
            key = request.GET.get('key')
            if key is None or not str(key).strip():
                return JsonResponse({'error': '参数错误', 'message': '当 mode=get 时，key 必填'}, status=400, json_dumps_params={'ensure_ascii': False})
            script_args.extend([mode, key])
        else:
            script_args.append(mode)
        try:
            result = subprocess.run(script_args, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            return_code = result.returncode
            stdout = result.stdout
            stderr = result.stderr.strip()
            if return_code != 0 or stderr:
                return JsonResponse({'error': '脚本执行失败', 'script': script_name, 'return_code': return_code, 'stdout': stdout if stdout else None, 'stderr': stderr if stderr else None}, status=500, json_dumps_params={'ensure_ascii': False})
            else:
                expected_format = SCRIPT_OUTPUT_FORMATS.get(mode, 'auto')
                if expected_format == 'json':
                    try:
                        json_data = json.loads(stdout)
                        return JsonResponse(json_data, safe=False, json_dumps_params={'ensure_ascii': False})
                    except json.JSONDecodeError:
                        return JsonResponse({'error': 'not json', 'output': stdout}, status=500)
                elif expected_format == 'text':
                    return HttpResponse(stdout, content_type='text/plain; charset=utf-8')
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
ALLOWED_OPERATION = ['autotime', 'settime']

def build_args_settime(script_path, data):
    TYPE = data.get('type')
    TIME = data.get('time')
    if TYPE not in ALLOWED_OPERATION:
        raise ValueError(f'type只允许为{ALLOWED_OPERATION}')
    if TYPE == 'settime' and (not TIME):
        raise ValueError('当type为settime时,time为必填')
    if TYPE == 'settime':
        return ['sh', script_path, TYPE, TIME]
    else:
        return ['sh', script_path, TYPE]

def build_args_hostname(script_path, data):
    pass
SCRIPT_REGISTRY = {'set_time.sh': build_args_settime, 'config.sh': build_args_hostname}

@login_required_api
@swagger_auto_schema(method='post', manual_parameters=[openapi.Parameter('script_name', openapi.IN_PATH, type=openapi.TYPE_STRING, description='脚本名', enum=list(SCRIPT_REGISTRY.keys()))], request_body=openapi.Schema(type=openapi.TYPE_OBJECT, properties={'type': openapi.Schema(type=openapi.TYPE_STRING, enum=ALLOWED_OPERATION, description='仅set_time.sh操作使用'), 'time': openapi.Schema(type=openapi.TYPE_STRING, description='时间,仅当type=settime时必填,格式:2025-09-01 12:00:00 +0800'), 'hostname': openapi.Schema(type=openapi.TYPE_STRING, description='主机名,仅config.sh操作使用')}), responses={200: openapi.Response('执行成功'), 400: openapi.Response('参数错误'), 404: openapi.Response('脚本不存在'), 500: openapi.Response('执行失败')})
@api_view(['POST'])
def set_time_hostname_api(request, script_name):
    """
    配置管理接口 - POST方法，用于系统时间及主机名修改
    """
    pass

@login_required_api
@swagger_auto_schema(method='post', operation_description='文件修改', manual_parameters=[openapi.Parameter(name='file_path', in_=openapi.IN_QUERY, description='文件名', required=True, type=openapi.TYPE_STRING, example='stdin_data.txt'), openapi.Parameter(name='dir_path', in_=openapi.IN_QUERY, description='目录路径', required=False, type=openapi.TYPE_STRING, example='configs/nginx')], request_body=openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_BINARY), responses={200: openapi.Response(description='写入成功', examples={'application/json': {'success': True, 'message': '字节数据写入成功', 'file_path': '/tmp/uploads/test.txt', 'file_size': '11 bytes'}}), 400: openapi.Response(description='参数错误'), 403: openapi.Response(description='权限不足'), 500: openapi.Response(description='写入失败')})
@api_view(['POST'])
@parser_classes([AnyBinaryParser])
def write_bytes_to_file(request):
    """
    接收字节数据并原样写入文件
    主要用于：
    1. 其他程序通过HTTP接口传输字节数据
    2. 从stdin重定向的数据
    3. 程序间数据传输
    """
    pass
