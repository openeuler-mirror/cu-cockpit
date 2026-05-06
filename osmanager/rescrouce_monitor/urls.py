from django.urls import path
from . import views

urlpatterns = [
    path('monitor/<str:script_name>', views.run_shell_script_api),
]
