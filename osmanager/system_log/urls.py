from django.urls import path
from .views import logs_view
from .views import boots_view

urlpatterns = [
    # 日志接口：GET
    path('logs/', logs_view, name='query logs'),
    path('boot/', boots_view, name='query boot_id'),
]

