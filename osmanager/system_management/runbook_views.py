from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view

from osmanager.auth.decorators import login_required_api

from .audit import record_audit
from .ai_provider import AIProviderError
from .ai_runbooks import (
    AIRunbookError,
    advance_runbook,
    cancel_runbook,
    confirm_runbook_step,
    create_runbook,
    generate_runbook,
    retry_runbook_step,
    serialize_runbook,
    skip_runbook_step,
)
from .ai_tools import AIToolValidationError
from .models import AIRunbook
from .permissions import get_session_identity


def _runbook_error(error, status=400):
    return JsonResponse(
        {'code': status, 'message': str(error)},
        status=status,
        json_dumps_params={'ensure_ascii': False},
    )


@login_required_api
@api_view(['GET'])
def runbook_list(request):
    identity = get_session_identity(request)
    queryset = AIRunbook.objects.filter(actor=identity.username).prefetch_related('steps')[:100]
    return JsonResponse({'items': [serialize_runbook(runbook) for runbook in queryset]})


@login_required_api
@api_view(['POST'])
def runbook_create(request):
    identity = get_session_identity(request)
    try:
        runbook = create_runbook(request.data, identity.username)
    except AIRunbookError as error:
        return _runbook_error(error)
    return JsonResponse({'runbook': serialize_runbook(runbook)})


@login_required_api
@api_view(['POST'])
def runbook_generate(request):
    identity = get_session_identity(request)
    try:
        runbook = generate_runbook(request.data.get('request'), identity.username)
    except (AIRunbookError, AIProviderError) as error:
        return _runbook_error(error)
    return JsonResponse({'runbook': serialize_runbook(runbook)})


@login_required_api
@api_view(['POST'])
def runbook_advance(request, runbook_id):
    runbook = get_object_or_404(AIRunbook, id=runbook_id)
    identity = get_session_identity(request)
    try:
        outcome = advance_runbook(runbook, identity.username, identity.is_admin)
    except (AIRunbookError, AIToolValidationError, RuntimeError) as error:
        record_audit(
            request, 'ai_runbook', 'advance', str(runbook.id), False, str(error),
            {'runbook_id': runbook.id, 'current_step': runbook.current_step},
        )
        return _runbook_error(error)
    record_audit(
        request, 'ai_runbook', 'advance', str(runbook.id), True, outcome['action'],
        {'runbook_id': runbook.id, 'action': outcome['action'], 'current_step': runbook.current_step},
    )
    return JsonResponse({
        'action': outcome['action'],
        'confirmation_token': outcome.get('confirmation_token'),
        'result': outcome.get('result'),
        'runbook': serialize_runbook(runbook),
    })


@login_required_api
@api_view(['POST'])
def runbook_confirm(request, runbook_id):
    runbook = get_object_or_404(AIRunbook, id=runbook_id)
    identity = get_session_identity(request)
    try:
        confirm_runbook_step(runbook, identity.username, request.data.get('confirmation_token'))
    except AIRunbookError as error:
        record_audit(
            request, 'ai_runbook', 'confirm_step', str(runbook.id), False, str(error),
            {'runbook_id': runbook.id, 'current_step': runbook.current_step},
        )
        return _runbook_error(error)
    record_audit(
        request, 'ai_runbook', 'confirm_step', str(runbook.id), True, 'Runbook 步骤已确认',
        {'runbook_id': runbook.id, 'current_step': runbook.current_step},
    )
    return JsonResponse({'runbook': serialize_runbook(runbook)})


@login_required_api
@api_view(['POST'])
def runbook_retry(request, runbook_id):
    runbook = get_object_or_404(AIRunbook, id=runbook_id)
    identity = get_session_identity(request)
    try:
        retry_runbook_step(runbook, identity.username)
    except AIRunbookError as error:
        record_audit(
            request, 'ai_runbook', 'retry_step', str(runbook.id), False, str(error),
            {'runbook_id': runbook.id, 'current_step': runbook.current_step},
        )
        return _runbook_error(error)
    record_audit(
        request, 'ai_runbook', 'retry_step', str(runbook.id), True, 'Runbook 步骤已重置',
        {'runbook_id': runbook.id, 'current_step': runbook.current_step},
    )
    return JsonResponse({'runbook': serialize_runbook(runbook)})


@login_required_api
@api_view(['POST'])
def runbook_skip(request, runbook_id):
    runbook = get_object_or_404(AIRunbook, id=runbook_id)
    identity = get_session_identity(request)
    try:
        skip_runbook_step(runbook, identity.username)
    except AIRunbookError as error:
        record_audit(
            request, 'ai_runbook', 'skip_step', str(runbook.id), False, str(error),
            {'runbook_id': runbook.id, 'current_step': runbook.current_step},
        )
        return _runbook_error(error)
    record_audit(
        request, 'ai_runbook', 'skip_step', str(runbook.id), True, 'Runbook 只读步骤已跳过',
        {'runbook_id': runbook.id, 'current_step': runbook.current_step},
    )
    return JsonResponse({'runbook': serialize_runbook(runbook)})


@login_required_api
@api_view(['POST'])
def runbook_cancel(request, runbook_id):
    runbook = get_object_or_404(AIRunbook, id=runbook_id)
    identity = get_session_identity(request)
    try:
        cancel_runbook(runbook, identity.username)
    except AIRunbookError as error:
        return _runbook_error(error)
    record_audit(
        request, 'ai_runbook', 'cancel', str(runbook.id), True, 'Runbook 已取消',
        {'runbook_id': runbook.id, 'current_step': runbook.current_step},
    )
    return JsonResponse({'runbook': serialize_runbook(runbook)})
