"""Session-authenticated inspection APIs; never collect inside an HTTP request."""

import json

from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST

from osmanager.auth.decorators import login_required_api

from .permissions import audited_admin_api, get_session_identity


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
    from django.http.response import HttpResponseBase

    try:
        result = operation()
        response = result if isinstance(result, HttpResponseBase) else JsonResponse(
            result, status=status)
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


def _page(request, queryset, serializer):
    """Return a bounded page from an explicitly ordered queryset."""
    if (set(request.GET) - {'page', 'limit'} or
            any(len(request.GET.getlist(key)) != 1 for key in request.GET)):
        raise ValueError('Expected only page and limit')
    page = int(request.GET.get('page', 1))
    limit = min(int(request.GET.get('limit', 20)), 100)
    if page < 1 or page > 1000000 or limit < 1:
        raise ValueError('Invalid inspection pagination')
    offset = (page - 1) * limit
    return {'items': [serializer(item) for item in queryset[offset:offset + limit]],
            'total': queryset.count(), 'page': page, 'limit': limit}


@login_required_api
@ensure_csrf_cookie
@require_GET
def overview(request):
    """Describe inspection availability without collecting host evidence."""
    from .inspection import INSPECTION_TEMPLATE
    from .inspection_runtime import worker_status

    identity = get_session_identity(request)
    return _respond(lambda: {
        'template': dict(INSPECTION_TEMPLATE), 'worker': worker_status(),
        'identity': identity.to_dict(), 'can_manage': identity.is_admin,
    })


@login_required_api
@require_GET
def plans(request):
    """List only the current actor's persisted plans in a stable order."""
    from .inspection_reports import serialize_plan
    from .models import InspectionPlan

    return _respond(lambda: _page(request, InspectionPlan.objects.filter(
        actor=get_session_identity(request).username).order_by('name', 'id'), serialize_plan))


@login_required_api
@require_GET
def runs(request):
    """List the current actor's stored runs without refreshing evidence."""
    from .inspection_reports import serialize_run
    from .models import InspectionRun

    return _respond(lambda: _page(request, InspectionRun.objects.filter(
        actor=get_session_identity(request).username).order_by('-queued_at', '-id'), serialize_run))


@login_required_api
@require_GET
def run_detail(request, run_id):
    """Return a stored run only when its actor matches the session identity."""
    from .inspection_reports import serialize_run
    from .models import InspectionRun

    return _respond(lambda: serialize_run(InspectionRun.objects.get(
        pk=run_id, actor=get_session_identity(request).username)))


@login_required_api
@require_GET
def report(request, run_id):
    """Download a private JSON or HTML report from the persisted run alone."""
    from django.http import HttpResponse
    from .inspection_reports import render_html_report, render_json_report
    from .models import InspectionRun

    if set(request.GET) - {'format'} or len(request.GET.getlist('format')) > 1:
        return _respond(lambda: (_ for _ in ()).throw(ValueError('Expected only one format')))
    report_format = request.GET.get('format', 'json')
    renderers = (render_json_report, render_html_report)
    return _respond(lambda: HttpResponse(
        renderers[('json', 'html').index(report_format)](InspectionRun.objects.get(
            pk=run_id, actor=get_session_identity(request).username)),
        content_type=('application/json; charset=utf-8' if report_format == 'json'
                      else 'text/html; charset=utf-8'),
        headers={
            'Content-Disposition': f'attachment; filename="inspection-{run_id}.{report_format}"',
        },
    ))


@audited_admin_api('inspection', 'plan_create')
@require_POST
def create_plan(request):
    """Persist an administrator's plan without collecting host evidence."""
    from .inspection_reports import serialize_plan
    from .inspection_schedules import save_plan

    return _respond(lambda: serialize_plan(save_plan(
        _payload(request), request.system_identity.username)), status=201)


@audited_admin_api('inspection', 'plan_update')
@require_POST
def edit_plan(request, plan_id):
    """Replace an owned plan through the validated schedule service."""
    from .inspection_reports import serialize_plan
    from .inspection_schedules import update_plan

    return _respond(lambda: serialize_plan(update_plan(
        plan_id, _payload(request), request.system_identity.username)))


def _enabled_payload(request):
    """Accept exactly one strict boolean for a plan's enabled state."""
    data = _payload(request)
    if set(data) != {'enabled'} or type(data['enabled']) is not bool:
        raise ValueError('Expected only a boolean enabled field')
    return data['enabled']


@audited_admin_api('inspection', 'plan_toggle')
@require_POST
def toggle_plan(request, plan_id):
    """Change an owned plan's enabled state without executing an inspection."""
    from .inspection_reports import serialize_plan
    from .inspection_schedules import set_plan_enabled

    return _respond(lambda: serialize_plan(set_plan_enabled(
        plan_id, _enabled_payload(request), request.system_identity.username)))