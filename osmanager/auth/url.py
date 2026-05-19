from django.urls import path
from .views import login_view, logout_view

urlpatterns = [
    path('login/', login_view, name='login'),      # 登录接口：POST
    path('logout/', logout_view, name='logout'),  # 登出接口：POST / GET
]
