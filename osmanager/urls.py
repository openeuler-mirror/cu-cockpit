"""
URL configuration for osmanager project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,include, re_path
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# 创建 schema 视图
schema_view = get_schema_view(
   openapi.Info(
      title="我的项目 API 文档",
      default_version='v1',
      description="这是我的 Django + DRF + drf-yasg 的接口文档，包含所有后端 API。",
      terms_of_service="https://example.com/terms/",
      contact=openapi.Contact(email="you@example.com"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/rescrouce/', include('osmanager.rescrouce_monitor.urls')),
    # 兼容旧前端构建包仍在请求 /api/run/monitor/... 的路径。
    path('api/run/', include('osmanager.rescrouce_monitor.urls')),
    path('api/config/', include('osmanager.config.urls')),
    path('api/auth/', include('osmanager.auth.url')),
    path('api/logs/', include('osmanager.system_log.urls')),
    path('api/terminal/', include('osmanager.web_terminal.urls')),
    path('api/service/', include('osmanager.service.urls')),
    # Swagger 相关 UI 页面
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    re_path(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    re_path(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
