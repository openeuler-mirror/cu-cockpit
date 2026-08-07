from django.http import JsonResponse
from rest_framework.decorators import api_view

from osmanager.auth.decorators import login_required_api

from .ai_planner import AIPlanValidationError, create_operation_plan, serialize_operation_plan
from .ai_provider import AIProviderError, provider_status
from .ai_tools import tool_catalog
from .permissions import get_session_identity


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
