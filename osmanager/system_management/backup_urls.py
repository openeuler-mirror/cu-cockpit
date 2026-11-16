"""Local backup center API routes."""

from django.urls import path

from . import backup_views


urlpatterns = [
    path('overview', backup_views.backup_overview, name='backup-overview'),
]