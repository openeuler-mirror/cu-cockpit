from django.urls import path
from . import views

urlpatterns = [
    path('manage', views.manage_service_api),
    path('status', views.get_service_status_api),
]

