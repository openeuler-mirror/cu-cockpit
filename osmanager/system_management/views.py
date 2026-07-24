from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view

from osmanager.auth.decorators import login_required_api

from .audit import record_audit
from .capabilities import detect_capabilities
from .config_center import (
    OperationConflict,
    SystemOperationError,
    create_group,
    create_user,
    delete_group,
    delete_user,
    get_ntp_status,
    get_selinux_status,
    list_accounts,
    set_selinux_mode,
    update_ntp,
    update_user,
)
from .models import ConfigSnapshot, OperationAudit
from .models import CronExecution, CronJob
from .cron import (
    ALLOWED_CRON_COMMANDS,
    create_job,
    delete_job,
    execute_job,
    serialize_execution,
    serialize_job,
    sync_cron_file,
    update_job,
)
from .permissions import admin_required_api, audited_admin_api, get_session_identity
from .processes import ProcessNotFound, get_process_detail, list_processes, send_process_signal
from .network import network_overview, update_firewall_rule
from .snapshots import diff_snapshot, registered_targets, rollback_snapshot


def _limit(request, default=100, maximum=500):
    try:
        return max(1, min(int(request.GET.get('limit', default)), maximum))
    except (TypeError, ValueError):
        return default


@login_required_api
@api_view(['GET'])
def session_context(request):
    return JsonResponse({'identity': get_session_identity(request).to_dict()})


@login_required_api
@api_view(['GET'])
def capabilities(request):
    return JsonResponse(detect_capabilities())


@admin_required_api
@api_view(['GET'])
def audit_list(request):
    queryset = OperationAudit.objects.all()
    module = request.GET.get('module', '').strip()
    if module:
        queryset = queryset.filter(module=module)
    items = list(queryset.values(
        'id', 'created_at', 'actor', 'client_ip', 'module', 'action', 'target', 'success', 'message', 'detail'
    )[:_limit(request)])
    return JsonResponse({'items': items})


@admin_required_api
@api_view(['GET'])
def snapshot_list(request):
    queryset = ConfigSnapshot.objects.all()
    target = request.GET.get('target', '').strip()
    if target:
        queryset = queryset.filter(target=target)
    items = list(queryset.values(
        'id', 'created_at', 'actor', 'module', 'target', 'path', 'checksum', 'reason', 'metadata'
    )[:_limit(request)])
    return JsonResponse({'items': items, 'targets': registered_targets()})


@admin_required_api
@api_view(['GET'])
def snapshot_diff(request, snapshot_id):
    snapshot = get_object_or_404(ConfigSnapshot, id=snapshot_id)
    try:
        difference = diff_snapshot(snapshot)
    except (OSError, UnicodeError, ValueError) as error:
        return JsonResponse({'code': 400, 'message': str(error)}, status=400,
                            json_dumps_params={'ensure_ascii': False})
    return JsonResponse({'id': snapshot.id, 'target': snapshot.target, 'diff': difference})


@admin_required_api
@api_view(['POST'])
def snapshot_rollback(request, snapshot_id):
    snapshot = get_object_or_404(ConfigSnapshot, id=snapshot_id)
    actor = get_session_identity(request).username
    try:
        current_snapshot = rollback_snapshot(snapshot, actor)
    except (OSError, UnicodeError, ValueError) as error:
        record_audit(request, 'foundation', 'snapshot_rollback', snapshot.target, False, str(error),
                     {'snapshot_id': snapshot.id})
        return JsonResponse({'code': 400, 'message': str(error)}, status=400,
                            json_dumps_params={'ensure_ascii': False})
    record_audit(request, 'foundation', 'snapshot_rollback', snapshot.target, True, '配置已回滚',
                 {'snapshot_id': snapshot.id, 'safety_snapshot_id': current_snapshot.id})
    return JsonResponse({'code': 200, 'message': '配置已回滚', 'safety_snapshot_id': current_snapshot.id},
                        json_dumps_params={'ensure_ascii': False})


def _operation_error(error):
    status = 409 if isinstance(error, OperationConflict) else 400
    return JsonResponse({'code': status, 'message': str(error)}, status=status,
                        json_dumps_params={'ensure_ascii': False})


@login_required_api
@api_view(['GET'])
def config_center_overview(request):
    accounts = list_accounts()
    return JsonResponse({
        'ntp': get_ntp_status(),
        'selinux': get_selinux_status(),
        'account_summary': {
            'users': len(accounts['users']),
            'groups': len(accounts['groups']),
            'login_shell_users': sum(1 for item in accounts['users'] if not item['system'] and item['shell'] in accounts['shells']),
        },
    })


@login_required_api
@api_view(['GET'])
def config_center_accounts(request):
    return JsonResponse(list_accounts())


@audited_admin_api('config_center', 'update_ntp')
@api_view(['POST'])
def config_center_update_ntp(request):
    try:
        status, snapshot = update_ntp(request.data, get_session_identity(request).username)
        return JsonResponse({'code': 200, 'message': 'NTP 配置已更新', 'ntp': status, 'snapshot_id': snapshot.id},
                            json_dumps_params={'ensure_ascii': False})
    except (OSError, UnicodeError, ValueError, SystemOperationError) as error:
        return _operation_error(error)


@audited_admin_api('config_center', 'create_user')
@api_view(['POST'])
def config_center_create_user(request):
    try:
        user = create_user(request.data)
        return JsonResponse({'code': 200, 'message': '用户已创建', 'username': user.pw_name},
                            json_dumps_params={'ensure_ascii': False})
    except (ValueError, SystemOperationError) as error:
        return _operation_error(error)


@audited_admin_api('config_center', 'update_user')
@api_view(['POST'])
def config_center_update_user(request, username):
    try:
        update_user(username, request.data)
        return JsonResponse({'code': 200, 'message': '用户已更新'}, json_dumps_params={'ensure_ascii': False})
    except (ValueError, SystemOperationError) as error:
        return _operation_error(error)


@audited_admin_api('config_center', 'delete_user')
@api_view(['POST'])
def config_center_delete_user(request, username):
    try:
        delete_user(username, bool(request.data.get('remove_home', False)))
        return JsonResponse({'code': 200, 'message': '用户已删除'}, json_dumps_params={'ensure_ascii': False})
    except (ValueError, SystemOperationError) as error:
        return _operation_error(error)


@audited_admin_api('config_center', 'create_group')
@api_view(['POST'])
def config_center_create_group(request):
    try:
        group = create_group(request.data.get('name'))
        return JsonResponse({'code': 200, 'message': '组已创建', 'name': group.gr_name},
                            json_dumps_params={'ensure_ascii': False})
    except (ValueError, SystemOperationError) as error:
        return _operation_error(error)


@audited_admin_api('config_center', 'delete_group')
@api_view(['POST'])
def config_center_delete_group(request, group_name):
    try:
        delete_group(group_name)
        return JsonResponse({'code': 200, 'message': '组已删除'}, json_dumps_params={'ensure_ascii': False})
    except (ValueError, SystemOperationError) as error:
        return _operation_error(error)


@audited_admin_api('config_center', 'set_selinux_mode')
@api_view(['POST'])
def config_center_set_selinux(request):
    try:
        status = set_selinux_mode(request.data.get('mode'))
        return JsonResponse({'code': 200, 'message': 'SELinux 运行态已更新', 'selinux': status},
                            json_dumps_params={'ensure_ascii': False})
    except (ValueError, SystemOperationError, OperationConflict) as error:
        return _operation_error(error)


@login_required_api
@api_view(['GET'])
def cron_jobs(request):
    items = [serialize_job(job) for job in CronJob.objects.all()]
    return JsonResponse({'items': items, 'allowed_commands': sorted(ALLOWED_CRON_COMMANDS)})


@login_required_api
@api_view(['GET'])
def cron_history(request):
    queryset = CronExecution.objects.all()
    job_id = request.GET.get('job_id')
    if job_id:
        queryset = queryset.filter(job_id=job_id)
    return JsonResponse({'items': [serialize_execution(item) for item in queryset[:_limit(request)] ]})


@audited_admin_api('cron', 'create_job')
@api_view(['POST'])
def cron_create(request):
    try:
        job = create_job(request.data, get_session_identity(request).username)
        return JsonResponse({'code': 200, 'message': '任务已创建', 'item': serialize_job(job)},
                            json_dumps_params={'ensure_ascii': False})
    except (ValueError, OSError) as error:
        return _operation_error(error)


@audited_admin_api('cron', 'update_job')
@api_view(['POST'])
def cron_update(request, job_id):
    job = get_object_or_404(CronJob, id=job_id)
    try:
        job = update_job(job, request.data, get_session_identity(request).username)
        return JsonResponse({'code': 200, 'message': '任务已更新', 'item': serialize_job(job)},
                            json_dumps_params={'ensure_ascii': False})
    except (ValueError, OSError) as error:
        return _operation_error(error)


@audited_admin_api('cron', 'delete_job')
@api_view(['POST'])
def cron_delete(request, job_id):
    job = get_object_or_404(CronJob, id=job_id)
    try:
        delete_job(job)
        return JsonResponse({'code': 200, 'message': '任务已删除'}, json_dumps_params={'ensure_ascii': False})
    except (ValueError, OSError) as error:
        return _operation_error(error)


@audited_admin_api('cron', 'run_job')
@api_view(['POST'])
def cron_run(request, job_id):
    job = get_object_or_404(CronJob, id=job_id)
    execution = execute_job(job, get_session_identity(request).username, manual=True)
    status = 200 if execution.status == 'success' else 400
    return JsonResponse({'code': status, 'message': f'执行状态: {execution.status}', 'execution': serialize_execution(execution)},
                        status=status, json_dumps_params={'ensure_ascii': False})


@login_required_api
@api_view(['GET'])
def process_list(request):
    try:
        limit = int(request.GET.get('limit', 500))
        data = list_processes(
            search=request.GET.get('search', ''),
            sort=request.GET.get('sort', 'cpu'),
            order=request.GET.get('order', 'desc'),
            limit=limit,
        )
        return JsonResponse(data)
    except (RuntimeError, ValueError) as error:
        return _operation_error(error)


@login_required_api
@api_view(['GET'])
def process_detail(request, pid):
    try:
        return JsonResponse({'item': get_process_detail(pid)})
    except ProcessNotFound as error:
        return JsonResponse({'code': 404, 'message': str(error)}, status=404,
                            json_dumps_params={'ensure_ascii': False})
    except ValueError as error:
        return _operation_error(error)


@audited_admin_api('process', 'send_signal')
@api_view(['POST'])
def process_signal(request, pid):
    try:
        detail, signal_name = send_process_signal(pid, request.data.get('signal'), request.data.get('confirm_pid'))
        return JsonResponse({
            'code': 200,
            'message': f'已向 PID {detail["pid"]} 发送 {signal_name}',
            'pid': detail['pid'],
            'name': detail['name'],
            'signal': signal_name,
        }, json_dumps_params={'ensure_ascii': False})
    except ProcessNotFound as error:
        return JsonResponse({'code': 404, 'message': str(error)}, status=404,
                            json_dumps_params={'ensure_ascii': False})
    except ValueError as error:
        return _operation_error(error)


@login_required_api
@api_view(['GET'])
def network_status(request):
    try:
        return JsonResponse(network_overview())
    except (RuntimeError, ValueError, SystemOperationError) as error:
        return _operation_error(error)


@audited_admin_api('network', 'update_firewall_rule')
@api_view(['POST'])
def firewall_rule_update(request):
    try:
        return JsonResponse({'code': 200, 'message': '防火墙规则已更新', 'firewall': update_firewall_rule(request.data)},
                            json_dumps_params={'ensure_ascii': False})
    except (ValueError, SystemOperationError, OperationConflict) as error:
        return _operation_error(error)