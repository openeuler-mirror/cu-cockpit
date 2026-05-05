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

@swagger_auto_schema(method='get', responses={200: openapi.Response(description='获取服务状态成功'), 400: openapi.Response(description='参数错误'), 404: openapi.Response(description='service_status.py 脚本未找到'), 408: openapi.Response(description='脚本执行超时'), 500: openapi.Response(description='获取服务状态失败'), 502: openapi.Response(description='脚本执行异常'), 503: openapi.Response(description='服务状态数据格式错误')})
@login_required_api
@api_view(['GET'])
def get_service_status_api(request):
    """
    获取系统服务状态接口
    直接调用 service_status.py 脚本
    """
    pass

@swagger_auto_schema(method='post', request_body=openapi.Schema(type=openapi.TYPE_OBJECT, required=['service_name', 'operation'], properties={'service_name': openapi.Schema(type=openapi.TYPE_STRING, description='服务名，如 nginx'), 'operation': openapi.Schema(type=openapi.TYPE_STRING, enum=['start', 'stop', 'restart', 'status'], description='操作')}), responses={200: 'OK', 404: 'not found manager_script', 400: '缺少必需参数', 401: '参数错误', 402: '脚本执行错误', 500: '操作异常'})
@login_required_api
@api_view(['POST'])
def manage_service_api(request):
    """
    服务管理接口 - POST方法，用于服务启动、停止、重启等操作
    """
    pass
