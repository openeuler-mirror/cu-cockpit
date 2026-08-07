from django.http import JsonResponse
from rest_framework.decorators import api_view

from osmanager.auth.decorators import login_required_api


def _runbook_error(error, status=400):
    return JsonResponse(
        {'code': status, 'message': str(error)},
        status=status,
        json_dumps_params={'ensure_ascii': False},
    )
