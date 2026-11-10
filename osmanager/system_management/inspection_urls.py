"""Read-only inspection routes beneath the system API."""

from django.urls import path

from . import inspection_views


urlpatterns = [
    path('overview', inspection_views.overview, name='inspection-overview'),
    path('plans', inspection_views.plans, name='inspection-plans'),
]