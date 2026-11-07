"""Administrator-only HTTP facade for local backup jobs."""

import json

from django.http import JsonResponse


def _error(code, message):
    return JsonResponse({'code': code, 'message': message}, status=code)


def _payload(request):
    if (request.content_type != 'application/json' or
            len(request.body) > 4096):
        raise ValueError('Bounded application/json body required')
    value = json.loads(request.body, parse_constant=lambda value: (_ for _ in ()).throw(
        ValueError('Non-JSON numeric constant')))
    if not isinstance(value, dict):
        raise ValueError('JSON object required')
    return value