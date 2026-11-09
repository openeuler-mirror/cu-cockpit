"""Session-authenticated inspection APIs; never collect inside an HTTP request."""

import json

from django.http import JsonResponse


def _payload(request):
    """Decode a JSON request object for inspection mutations."""
    return json.loads(request.body)