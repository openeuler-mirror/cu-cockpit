from django.urls import path
from . import views

urlpatterns = [
    path('connect', views.terminal_connect, name='terminal_connect'),
    path('check', views.auth_check, name='auth_check'),
    path('token', views.csrf_token, name='token'),
]
