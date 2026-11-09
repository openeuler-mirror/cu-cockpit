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
    from zoneinfo import ZoneInfoNotFoundError
    from django.core.exceptions import ObjectDoesNotExist
    from django.db import DatabaseError, IntegrityError

    try:
        response = JsonResponse(operation(), status=status)
    except (ValueError, UnicodeDecodeError, ZoneInfoNotFoundError) as error:
        code = 409 if str(error) in (
            'Inspection plan limit reached (64)', 'Inspection queue limit reached (64)',
        ) else 400
        response = JsonResponse({'code': code, 'message': 'Inspection capacity reached' if
                                 code == 409 else 'Invalid inspection request'}, status=code)
    except ObjectDoesNotExist:
        response = JsonResponse({'code': 404, 'message': 'Inspection resource not found'}, status=404)
    except (IntegrityError, BlockingIOError):
        response = JsonResponse({'code': 409, 'message': 'Inspection state is busy'}, status=409)
    except (DatabaseError, OSError):
        response = JsonResponse({'code': 503, 'message': 'Inspection storage unavailable'}, status=503)
    response['Cache-Control'] = 'private, no-store'
    return response