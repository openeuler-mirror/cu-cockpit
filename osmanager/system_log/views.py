import os
import sys
import json
import subprocess
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from osmanager.auth.decorators import login_required_api
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_SCRIPT_PATH = os.path.abspath(os.path.join(BASE_DIR, 'manager-script', 'log.py'))
BOOT_SCRIPT_PATH = os.path.abspath(os.path.join(BASE_DIR, 'manager-script', 'boot_offset.py'))

def _build_cmd_from_request(request):
    """
    把查询参数转成log.py的命令行参数
    支持: since, until, priority(-p), service(-s), limit(-n), keyword(-g), boot(-b)
    强制 --format json，方便接口返回 JSON
    """
    cmd = [sys.executable or 'python3', LOG_SCRIPT_PATH]

    def add_arg(flag, value):
        pass
    params = request.GET if request.method == 'GET' else request.POST
    add_arg('--since', params.get('since'))
    add_arg('--until', params.get('until'))
    add_arg('-p', params.get('priority'))
    add_arg('-s', params.get('service'))
    add_arg('-n', params.get('limit'))
    add_arg('-g', params.get('keyword'))
    add_arg('-b', params.get('boot'))
    add_arg('-t', params.get('identifier'))
    add_arg('--cursor', params.get('cursor'))
    add_arg('--output_format', params.get('output_format'))
    return cmd

@swagger_auto_schema(method='get', operation_summary='获取可用的引导偏移列表', operation_description='journalctl --list-boots返回可用的引导偏移号数组，如 [0, -1, -2]', responses={200: openapi.Response(description='成功返回', schema=openapi.Schema(type=openapi.TYPE_OBJECT, properties={'boots': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_INTEGER), example=[0, -1, -2, -3]), 'count': openapi.Schema(type=openapi.TYPE_INTEGER, example=4)})), 404: openapi.Response(description='脚本不存在', schema=openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING)})), 500: openapi.Response(description='服务端错误', schema=openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING), 'stderr': openapi.Schema(type=openapi.TYPE_STRING), 'cmd': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING))}))}, tags=['system boot'])
@login_required_api
@api_view(['GET'])
def boots_view(request):
    pass

@swagger_auto_schema(method='get', operation_summary='查询系统日志', operation_description='根据指定条件查询系统日志，支持按时间、优先级、服务名等条件过滤', manual_parameters=[openapi.Parameter('output_format', openapi.IN_QUERY, description='日志输出形式', type=openapi.TYPE_STRING, enum=['summary', 'all_json'], example='summary'), openapi.Parameter('cursor', openapi.IN_QUERY, description='指定cursor获取元数据信息', type=openapi.TYPE_STRING, example='s=;i=;b=;m=;t=;x='), openapi.Parameter('since', openapi.IN_QUERY, description='开始时间，支持多种格式如 "2025-09-01 10:00:00" 或 "1h ago"', type=openapi.TYPE_STRING, example='2025-08-18 00:00:00'), openapi.Parameter('until', openapi.IN_QUERY, description='结束时间，如 "2025-09-01 12:00:00" 或 "now"', type=openapi.TYPE_STRING, example='2025-08-19 23:59:59'), openapi.Parameter('priority', openapi.IN_QUERY, description='日志优先级，如 "err", "info", "0..7"', type=openapi.TYPE_STRING, enum=['err', 'info', 'warning', 'debug', 'emerg', 'crit', 'notice', 'alert', '0', '1', '2', '3', '4', '5', '6', '7'], example='err'), openapi.Parameter('service', openapi.IN_QUERY, description='服务名/Unit，如 "nginx" 或 "nginx.service"', type=openapi.TYPE_STRING, example='sshd'), openapi.Parameter('identifier', openapi.IN_QUERY, description='按SYSLOG_IDENTIFIER过滤，如 sshd', type=openapi.TYPE_STRING, example='sshd'), openapi.Parameter('keyword', openapi.IN_QUERY, description='关键字/正则表达式搜索', type=openapi.TYPE_STRING, example='failed'), openapi.Parameter('limit', openapi.IN_QUERY, description='显示行数限制', type=openapi.TYPE_INTEGER, example=100), openapi.Parameter('boot', openapi.IN_QUERY, description='引导选择，"-1" 表示上一引导，"0" 表示当前引导，或指定boot ID', type=openapi.TYPE_STRING, example='0')], responses={200: openapi.Response(description='成功返回日志数据', schema=openapi.Schema(type=openapi.TYPE_OBJECT, properties={'logs': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT, properties={'date': openapi.Schema(type=openapi.TYPE_STRING, example='Sep 09'), 'time': openapi.Schema(type=openapi.TYPE_STRING, example='10:23:09'), 'hostname': openapi.Schema(type=openapi.TYPE_STRING, example='bigdata1'), 'service': openapi.Schema(type=openapi.TYPE_STRING, example='PackageKit'), 'pid': openapi.Schema(type=openapi.TYPE_INTEGER, example=2177658), 'message': openapi.Schema(type=openapi.TYPE_STRING, example='message content'), 'raw': openapi.Schema(type=openapi.TYPE_STRING, example='raw log line')})), 'count': openapi.Schema(type=openapi.TYPE_INTEGER, example=10)})), 500: openapi.Response(description='服务器错误', schema=openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, example='服务内部异常'), 'returncode': openapi.Schema(type=openapi.TYPE_INTEGER, example=1), 'stderr': openapi.Schema(type=openapi.TYPE_STRING, example='error message'), 'cmd': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING))})), 504: openapi.Response(description='请求超时', schema=openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING, example='调用log.py超时(60s)')}))}, tags=['systemd logs'])
@login_required_api
@api_view(['GET'])
def logs_view(request):
    """
    GET /api/logs?service=sshd&priority=err&since=2025-08-01&until=2025-09-09&limit=200
    直接调用 log.py 并返回 JSON
    """
    pass
