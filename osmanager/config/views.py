# -*- coding: utf-8 -*-
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
    media_type = '*/*'  # 接受所有类型
    def parse(self, stream, media_type=None, parser_context=None):
        return stream.read()

ALLOWED_SCRIPT_MODES = {
    'config.sh': ['sshkey','gethostname','time','get']
}

# 不同参数返回格式限制
SCRIPT_OUTPUT_FORMATS = {
    'sshkey': 'json',
    'gethostname': 'text',
    'time': 'json',
    'get': 'text'
}
ALLOWED_SCRIPTS = list(ALLOWED_SCRIPT_MODES.keys())

@swagger_auto_schema(
    method='get',
    manual_parameters=[
        openapi.Parameter('script_name', openapi.IN_PATH, type=openapi.TYPE_STRING,
                          description="脚本名", enum=ALLOWED_SCRIPTS),
        openapi.Parameter('mode', openapi.IN_QUERY, type=openapi.TYPE_STRING,
                          description="参数：config.sh -> ['sshkey','gethostname','time','get']",
                          enum=sorted({m for v in ALLOWED_SCRIPT_MODES.values() for m in v})),
        openapi.Parameter(
            'key',
            openapi.IN_QUERY,
            description="当 mode=get 时必填；例如：/?mode=get&key=bashrc",
            type=openapi.TYPE_STRING,
            required=False,  # 条件必填：在描述里说明
        ),
    ],
    responses={
      200: openapi.Response(description="执行成功"),
      404: openapi.Response(description="脚本未找到"),
      400: openapi.Response(description="传参错误"),
      500: openapi.Response(description="脚本执行失败"),
      408: openapi.Response(description="超时"),
      501: openapi.Response(description="调用脚本执行失败"),
      502: openapi.Response(description="位置错误"),
}
)
@login_required_api
@api_view(['GET'])
def get_config_api(request, script_name):
    # 脚本存放的目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    SCRIPTS_DIR = os.path.join(current_dir, 'manager-script')

    # 拼接脚本的完整路径
    script_path = os.path.join(SCRIPTS_DIR, script_name)

    # 检查脚本是否存在
    if not os.path.isfile(script_path):
        return Response({
            "error": "not found manager_script",
            "script": script_name,
            "script_path": script_path
        }, status=404)
    try:
        # 根据脚本扩展名决定执行方式
        script_extension = os.path.splitext(script_name)[1].lower()

        if script_extension == '.py':
            # Python脚本使用python命令执行
            script_args = ['python3', script_path]
        elif script_extension == '.sh':
            # Shell脚本使用bash命令执行
            script_args = ['bash', script_path]
        else:
            # 默认尝试作为shell脚本执行
            script_args = ['bash', script_path]

        # 从 URL 查询参数中获取 mode（比如 ?mode=all）
        mode = request.GET.get('mode')

        # 允许的 mode 列表
        allowed_modes = ALLOWED_SCRIPT_MODES['config.sh']
        if mode is None or not str(mode).strip():  # 未提供或空字符串
            return JsonResponse({"error": "参数错误", "message": "mode 必填且不能为空"}, status=400, json_dumps_params={'ensure_ascii': False})
        if mode not in allowed_modes:
            return JsonResponse({"error": "参数错误", "message": f"mode 只允许为 {allowed_modes}，你传入的是: {mode}"}, status=400, json_dumps_params={'ensure_ascii': False})
        # 组装脚本参数
        if mode == 'get':
            key = request.GET.get('key')  # 示例：/?mode=get&key=bashrc
            if key is None or not str(key).strip():
                return JsonResponse({"error": "参数错误", "message": "当 mode=get 时，key 必填"}, status=400, json_dumps_params={'ensure_ascii': False})
            script_args.extend([mode, key])
        else:
            script_args.append(mode)
        try:
            result = subprocess.run(
                script_args,
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # 获取脚本的返回码和输出
            return_code = result.returncode
            stdout = result.stdout
            stderr = result.stderr.strip()

            # 查询类脚本可能把兼容性告警写到 stderr；只按返回码判定失败。
            if return_code != 0:
                return JsonResponse({
                    "error": "脚本执行失败",
                    "script": script_name,
                    "return_code": return_code,
                    "stdout": stdout if stdout else None,
                    "stderr": stderr if stderr else None
                }, status=500, json_dumps_params={'ensure_ascii': False})
            else:
                expected_format = SCRIPT_OUTPUT_FORMATS.get(mode, 'auto')

                if expected_format == 'json':
                    # 强制要求 JSON 格式
                    try:
                        json_data = json.loads(stdout)
                        return JsonResponse(json_data, safe=False,
                                        json_dumps_params={'ensure_ascii': False})
                    except json.JSONDecodeError:
                        return JsonResponse({"error": "not json",
                                             "output": stdout}, status=500)
                elif expected_format == 'text':
                    return HttpResponse(stdout, content_type='text/plain; charset=utf-8')

        except subprocess.TimeoutExpired as e:
            return JsonResponse({
                "error": "脚本执行超时",
                "script": script_name,
                "details": str(e)
            }, status=408, json_dumps_params={'ensure_ascii': False})
        except FileNotFoundError as e:
            return JsonResponse({
                "error": "脚本文件未找到或bash命令不存在",
                "script": script_name,
                "details": str(e)
            }, status=404, json_dumps_params={'ensure_ascii': False})
        except Exception as e:
            return JsonResponse({
                "error": "脚本执行异常",
                "script": script_name,
                "details": str(e)
            }, status=500, json_dumps_params={'ensure_ascii': False})
    except subprocess.CalledProcessError as e:
        return JsonResponse({
            "error": "调用脚本执行失败",
            "script": script_name,
            "stderr": e.stderr.strip()
        }, status=500, json_dumps_params={'ensure_ascii': False})
    except Exception as e:
        return JsonResponse({
            "error": "未知错误",
            "details": str(e),
            "script": script_name
        }, status=500, json_dumps_params={'ensure_ascii': False})

ALLOWED_OPERATION = ['autotime','settime']
def build_args_settime(script_path, data):
    TYPE = data.get('type')
    TIME = data.get('time')
    if TYPE not in ALLOWED_OPERATION:
        raise ValueError(f"type只允许为{ALLOWED_OPERATION}")
    if TYPE == 'settime' and not TIME:
        raise ValueError("当type为settime时,time为必填")
    if TYPE == 'settime':
        return ['sh', script_path, TYPE, TIME]  # TIME作为单独参数，不会被拆分
    else:
        return ['sh', script_path, TYPE]

def build_args_hostname(script_path, data):
    hostname = data.get('hostname')
    if not hostname:
        raise ValueError("hostname必填")
    return ['sh', script_path, 'sethostname', hostname]

SCRIPT_REGISTRY = {
    'set_time.sh': build_args_settime,
    'config.sh': build_args_hostname,
}
@login_required_api
@swagger_auto_schema(
    method='post',
    manual_parameters=[
        openapi.Parameter(
            'script_name', openapi.IN_PATH,
            type=openapi.TYPE_STRING,
            description='脚本名',
            enum=list(SCRIPT_REGISTRY.keys()),
        ),
    ],
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'type': openapi.Schema(type=openapi.TYPE_STRING,
                                        enum=ALLOWED_OPERATION,
                                        description='仅set_time.sh操作使用'),
            'time': openapi.Schema(type=openapi.TYPE_STRING, description='时间,仅当type=settime时必填,格式:2025-09-01 12:00:00 +0800'),
            'hostname': openapi.Schema(
                type=openapi.TYPE_STRING,
                description='主机名,仅config.sh操作使用'
            ),

        },
    ),
    responses={
        200: openapi.Response('执行成功'),
        400: openapi.Response('参数错误'),
        404: openapi.Response('脚本不存在'),
        500: openapi.Response('执行失败'),
    }
)
@api_view(['POST'])
def set_time_hostname_api(request, script_name):
    """
    配置管理接口 - POST方法，用于系统时间及主机名修改
    """
    # 脚本存放的目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    SCRIPTS_DIR = os.path.join(current_dir, 'manager-script')
    script_path = os.path.join(SCRIPTS_DIR, script_name)
    if script_name not in SCRIPT_REGISTRY:
        return JsonResponse({"error": "不支持的脚本", "script": script_name},
                            status=400, json_dumps_params={'ensure_ascii': False})
    if not os.path.isfile(script_path):
        return JsonResponse({
            "error": "not found manager_script",
            "script_path": script_path
        }, status=404)
    try:
        build_args = SCRIPT_REGISTRY[script_name]
        args = build_args(script_path, request.data)
        result = subprocess.run(
            args,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30
        )

        return_code = result.returncode
        stdout = (result.stdout or '').strip()
        stderr = (result.stderr or '').strip()


        response_data = {
            "script": script_name,
            "return_code": return_code,
            "success_flag": return_code == 0
        }
        if stdout:
            response_data["output"] = stdout
        if return_code == 0:
            response_data["message"] = f"操作成功"
            return JsonResponse(response_data, status=200, json_dumps_params={'ensure_ascii': False})
        elif return_code != 0 or stderr:
            response_data["message"] = f"操作失败"
            response_data["error"] = stderr if stderr else "未知错误"
            return JsonResponse(response_data, status=500, json_dumps_params={'ensure_ascii': False})

    except ValueError as ve:
        return JsonResponse({"error": "参数错误", "message": str(ve)}, status=400, json_dumps_params={'ensure_ascii': False})
    except Exception as e:
        return JsonResponse({
            "error": "操作异常",
            "message": f"配置管理发生异常: {str(e)}",
        }, status=500, json_dumps_params={'ensure_ascii': False})


@login_required_api
@swagger_auto_schema(
    method='post',
    operation_description="文件修改",
    manual_parameters=[
        openapi.Parameter(
            name='file_path',
            in_=openapi.IN_QUERY,
            description='文件名',
            required=True,
            type=openapi.TYPE_STRING,
            example='stdin_data.txt'  # 示例文件名
        ),
        openapi.Parameter(
            name='dir_path',
            in_=openapi.IN_QUERY,
            description='目录路径',
            required=False,
            type=openapi.TYPE_STRING,
            example='configs/nginx'  # 示例目录
        ),
    ],
    request_body=openapi.Schema(
        type=openapi.TYPE_STRING,
        format=openapi.FORMAT_BINARY
    ),
    responses={
        200: openapi.Response(
            description="写入成功",
            examples={
                "application/json": {
                    "success": True,
                    "message": "字节数据写入成功",
                    "file_path": "/tmp/uploads/test.txt",
                    "file_size": "11 bytes"
                }
            }
        ),
        400: openapi.Response(description="参数错误"),
        403: openapi.Response(description="权限不足"),
        500: openapi.Response(description="写入失败")
    }
)

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
    try:
        file_path = request.query_params.get('file_path')  # 只从URL取，避免触发body解析
        if not file_path:
            return Response({"error": "缺少必要参数", "message": "请在URL查询参数提供 file_path"}, status=400)

        base_dir = request.query_params.get('dir_path')  # 只从URL取，避免触发body解析
        if not base_dir:
            base_dir = os.path.expanduser('~')
        safe_path = os.path.join(base_dir, file_path.lstrip('/'))
        p = Path(safe_path)
        # 创建目录（如果不存在）
        if p.parent and not p.parent.exists():
            p.parent.mkdir(parents=True, exist_ok=True)

        data = request.data
        if not isinstance(data, (bytes, bytearray)):
            return Response({"error": "数据错误", "message": "未接收到二进制数据"}, status=400)

        with p.open("wb") as f:
            f.write(data)

        file_size = p.stat().st_size if p.exists() else 0
        return JsonResponse({
            "success": True,
            "message": "修改成功",
            "file_path": safe_path,
            "file_size": f"{file_size} bytes"
        }, json_dumps_params={'ensure_ascii': False})
    except PermissionError as e:
        return JsonResponse({
            "error": "权限不足",
            "message": f"无法写入文件: {str(e)}"
        }, status=status.HTTP_403_FORBIDDEN, json_dumps_params={'ensure_ascii': False})
    except Exception as e:
        return JsonResponse({
            "error": "写入失败",
            "message": str(e)
        }, status=500, json_dumps_params={'ensure_ascii': False})

