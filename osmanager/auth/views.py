from django.contrib.auth import logout
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.sessions.backends.db import SessionStore
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .auth_pam import verify_with_pam, PamNotAvailable, PamAuthError

@swagger_auto_schema(method='post', operation_summary='用户登录', operation_description='使用用户名和密码进行登录验证', request_body=openapi.Schema(type=openapi.TYPE_OBJECT, properties={'username': openapi.Schema(type=openapi.TYPE_STRING, description='用户名', example='admin'), 'password': openapi.Schema(type=openapi.TYPE_STRING, description='密码', example='123456')}, required=['username', 'password']), responses={200: openapi.Response(description='登录成功', examples={'application/json': {'code': 200, 'message': '登录成功', 'user': 'admin'}}), 400: openapi.Response(description='请求错误', examples={'application/json': {'code': 400, 'message': '请输入用户名和密码'}}), 401: openapi.Response(description='认证失败', examples={'application/json': {'code': 401, 'message': '用户名或密码错误'}})})
@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    if request.method == 'POST':
        username = request.data.get('username') if hasattr(request, 'data') else request.POST.get('username')
        password = request.data.get('password') if hasattr(request, 'data') else request.POST.get('password')
        if not username or not password:
            return Response({'code': 400, 'message': '请输入用户名和密码'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            auth_login = verify_with_pam(username, password, service='login')
        except PamNotAvailable:
            return Response({'code': 500, 'message': '认证服务不可用，请安装系统包python3-pam'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except PamAuthError as e:
            return Response({'code': 500, 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        if auth_login:
            request.session['username'] = username
            return Response({'code': 200, 'message': '登录成功', 'user': username})
        else:
            return Response({'code': 401, 'message': '用户名或密码错误'}, status=status.HTTP_401_UNAUTHORIZED)
    return Response({'code': 400, 'message': '请使用POST请求'}, status=status.HTTP_400_BAD_REQUEST)

@swagger_auto_schema(method='post', operation_summary='用户登出', operation_description='清除用户会话，退出登录', responses={200: openapi.Response(description='登出成功', examples={'application/json': {'code': 200, 'message': '登出成功'}}), 400: openapi.Response(description='登出失败', examples={'application/json': {'code': 500, 'message': '登出失败'}})})
@api_view(['POST'])
@permission_classes([AllowAny])
def logout_view(request):
    pass
