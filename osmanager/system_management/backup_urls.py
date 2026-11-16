"""Local backup center API routes."""

from django.urls import path

from . import backup_views


urlpatterns = [
    path('overview', backup_views.backup_overview, name='backup-overview'),
    path('create', backup_views.backup_create, name='backup-create'),
    path('import', backup_views.backup_import, name='backup-import'),
    path('schedule', backup_views.backup_schedule, name='backup-schedule'),
    path('verify', backup_views.backup_verify, name='backup-verify'),
    path('download/<str:archive_id>', backup_views.backup_download, name='backup-download'),
    path('restore/preflight', backup_views.backup_restore_preflight, name='backup-restore-preflight'),
    path('restore/confirm', backup_views.backup_restore_confirm, name='backup-restore-confirm'),
]