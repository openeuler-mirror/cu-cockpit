from django.http import JsonResponse
from rest_framework.decorators import api_view

from osmanager.auth.decorators import login_required_api

from .ai_runbooks import serialize_runbook
from .models import AIRunbook
from .permissions import get_session_identity


def _runbook_error(error, status=400):
    return JsonResponse(
        {'code': status, 'message': str(error)},
        status=status,
        json_dumps_params={'ensure_ascii': False},
    )


@login_required_api
@api_view(['GET'])
def runbook_list(request):
    identity = get_session_identity(request)
    queryset = AIRunbook.objects.filter(actor=identity.username).prefetch_related('steps')[:100]
    return JsonResponse({'items': [serialize_runbook(runbook) for runbook in queryset]})
