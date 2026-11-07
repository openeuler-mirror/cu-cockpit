"""Administrator-only HTTP facade for local backup jobs."""

import json

from django.http import JsonResponse


def _error(code, message):
    return JsonResponse({'code': code, 'message': message}, status=code)


def _payload(request):
    value = json.loads(request.body)
    if not isinstance(value, dict):
        raise ValueError('JSON object required')
    return value