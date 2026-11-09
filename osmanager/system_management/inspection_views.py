"""Session-authenticated inspection APIs; never collect inside an HTTP request."""

import json

from django.http import JsonResponse


def _payload(request):
    """Decode a JSON request object for inspection mutations."""
    if request.GET or request.content_type != 'application/json' or len(request.body) > 4096:
        raise ValueError('Bounded application/json object without query parameters required')
    data = json.loads(request.body, parse_constant=lambda value: (_ for _ in ()).throw(
        ValueError('Non-JSON numeric constant')))
    if not isinstance(data, dict):
        raise ValueError('JSON object required')
    return data


def _respond(operation, status=200):
    """Produce a private JSON response from one inspection operation."""
    response = JsonResponse(operation(), status=status)
    response['Cache-Control'] = 'private, no-store'
    return response