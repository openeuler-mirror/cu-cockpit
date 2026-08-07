from django.http import JsonResponse
from rest_framework.decorators import api_view

from osmanager.auth.decorators import login_required_api

from .ai_provider import provider_status
from .ai_tools import tool_catalog


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
