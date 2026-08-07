from django.http import JsonResponse
from rest_framework.decorators import api_view

from osmanager.auth.decorators import login_required_api

from .ai_provider import provider_status
from .ai_tools import tool_catalog


@login_required_api
@api_view(['GET'])
def ai_status(request):
    return JsonResponse({'provider': provider_status(), 'tools': tool_catalog()})
