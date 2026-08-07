from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view

from osmanager.auth.decorators import login_required_api

from .audit import record_audit
from .ai_analysis import AIAnalysisError, analyze_logs, explain_command_output, review_config_diff
from .ai_planner import (
    AIPlanValidationError,
    create_operation_plan,
    execute_operation_plan,
    serialize_operation_plan,
)
from .ai_provider import AIProviderError, provider_status
from .ai_tools import AIToolExecutionContext, AIToolValidationError, tool_catalog
from .models import AIOperationPlan, ConfigSnapshot
from .permissions import get_session_identity
from .snapshots import diff_snapshot


def _ai_error(error, status=400):
    return JsonResponse(
        {'code': status, 'message': str(error)},
        status=status,
        json_dumps_params={'ensure_ascii': False},
    )


@login_required_api
@api_view(['GET'])
def ai_status(request):
    return JsonResponse({'provider': provider_status(), 'tools': tool_catalog()})


@login_required_api
@api_view(['POST'])
def ai_plan_create(request):
    identity = get_session_identity(request)
    try:
        plan = create_operation_plan(request.data.get('request'), identity.username)
    except (AIPlanValidationError, AIProviderError) as error:
        return _ai_error(error)
    return JsonResponse({'plan': serialize_operation_plan(plan)})


@login_required_api
@api_view(['POST'])
def ai_plan_execute(request, plan_id):
    plan = get_object_or_404(AIOperationPlan, id=plan_id)
    identity = get_session_identity(request)
    context = AIToolExecutionContext(
        actor=identity.username,
        is_admin=identity.is_admin,
        confirmed=request.data.get('confirmed') is True,
    )
    try:
        execute_operation_plan(plan, context)
    except (AIPlanValidationError, AIToolValidationError, RuntimeError) as error:
        record_audit(
            request, 'ai', 'execute_plan', str(plan.id), False, str(error),
            {'plan_id': plan.id, 'tool': plan.tool_calls[0]['tool'], 'risk': plan.risk},
        )
        return _ai_error(error)
    record_audit(
        request, 'ai', 'execute_plan', str(plan.id), True, 'AI 计划执行成功',
        {'plan_id': plan.id, 'tool': plan.tool_calls[0]['tool'], 'risk': plan.risk},
    )
    return JsonResponse({'plan': serialize_operation_plan(plan)})


@login_required_api
@api_view(['POST'])
def ai_logs_analyze(request):
    try:
        return JsonResponse(analyze_logs(request.data.get('logs')))
    except (AIAnalysisError, AIProviderError) as error:
        return _ai_error(error)


@login_required_api
@api_view(['POST'])
def ai_output_explain(request):
    try:
        return JsonResponse(explain_command_output(request.data.get('output')))
    except (AIAnalysisError, AIProviderError) as error:
        return _ai_error(error)


@login_required_api
@api_view(['POST'])
def ai_config_review(request):
    snapshot = get_object_or_404(ConfigSnapshot, id=request.data.get('snapshot_id'))
    try:
        return JsonResponse(review_config_diff(snapshot.target, diff_snapshot(snapshot)))
    except (OSError, UnicodeError, ValueError, AIAnalysisError, AIProviderError) as error:
        return _ai_error(error)
