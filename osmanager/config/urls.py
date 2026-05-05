from django.urls import path
from . import views

urlpatterns = [
    path('update/', views.write_bytes_to_file),
    path('get/<str:script_name>', views.get_config_api),
    path('set/<str:script_name>', views.set_time_hostname_api),
]
