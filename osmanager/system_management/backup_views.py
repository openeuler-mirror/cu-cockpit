"""Administrator-only HTTP facade for local backup jobs."""

from django.http import JsonResponse


def _error(code, message):
    return JsonResponse({'code': code, 'message': message}, status=code)