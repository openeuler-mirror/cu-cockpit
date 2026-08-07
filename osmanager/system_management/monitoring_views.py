from django.http import JsonResponse
from rest_framework.decorators import api_view

from osmanager.auth.decorators import login_required_api


def _bounded_int(value, default, minimum, maximum):
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return max(minimum, min(parsed, maximum))
