from django.urls import path

from . import ai_views, monitoring_views, runbook_views, views


urlpatterns = [
    path('context', views.session_context, name='system-context'),
    path('capabilities', views.capabilities, name='system-capabilities'),
    path('audits', views.audit_list, name='system-audits'),
    path('snapshots', views.snapshot_list, name='system-snapshots'),
    path('snapshots/<int:snapshot_id>/diff', views.snapshot_diff, name='system-snapshot-diff'),
    path('snapshots/<int:snapshot_id>/rollback', views.snapshot_rollback, name='system-snapshot-rollback'),
    path('config-center/overview', views.config_center_overview, name='config-center-overview'),
    path('config-center/accounts', views.config_center_accounts, name='config-center-accounts'),
    path('config-center/ntp/update', views.config_center_update_ntp, name='config-center-update-ntp'),
    path('config-center/users', views.config_center_create_user, name='config-center-create-user'),
    path('config-center/users/<str:username>/update', views.config_center_update_user, name='config-center-update-user'),
    path('config-center/users/<str:username>/delete', views.config_center_delete_user, name='config-center-delete-user'),
    path('config-center/groups', views.config_center_create_group, name='config-center-create-group'),
    path('config-center/groups/<str:group_name>/delete', views.config_center_delete_group, name='config-center-delete-group'),
    path('config-center/selinux/mode', views.config_center_set_selinux, name='config-center-set-selinux'),
    path('cron/jobs', views.cron_jobs, name='cron-jobs'),
    path('cron/history', views.cron_history, name='cron-history'),
    path('cron/jobs/create', views.cron_create, name='cron-create'),
    path('cron/jobs/<int:job_id>/update', views.cron_update, name='cron-update'),
    path('cron/jobs/<int:job_id>/delete', views.cron_delete, name='cron-delete'),
    path('cron/jobs/<int:job_id>/run', views.cron_run, name='cron-run'),
    path('processes', views.process_list, name='process-list'),
    path('processes/<int:pid>', views.process_detail, name='process-detail'),
    path('processes/<int:pid>/signal', views.process_signal, name='process-signal'),
    path('network/overview', views.network_status, name='network-overview'),
    path('network/firewall/rules/update', views.firewall_rule_update, name='firewall-rule-update'),
]