from datetime import timedelta

from django.db import IntegrityError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.decorators import api_view

from osmanager.auth.decorators import login_required_api

from .alerts import (
    AlertRuleValidationError,
    create_alert_rule,
    serialize_alert_rule,
    set_alert_rule_enabled,
)
from .models import AlertRule, MetricSample
from .monitoring import serialize_metric_sample
from .permissions import audited_admin_api


def _bounded_int(value, default, minimum, maximum):
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return max(minimum, min(parsed, maximum))


@login_required_api
@api_view(['GET'])
def metric_samples(request):
    hours = _bounded_int(request.GET.get('hours'), 24, 1, 720)
    limit = _bounded_int(request.GET.get('limit'), 500, 1, 5000)
    queryset = MetricSample.objects.filter(collected_at__gte=timezone.now() - timedelta(hours=hours))
    samples = list(queryset[:limit])
    samples.reverse()
    return JsonResponse({'items': [serialize_metric_sample(sample) for sample in samples]})


@login_required_api
@api_view(['GET'])
def alert_rules(request):
    return JsonResponse({'items': [serialize_alert_rule(rule) for rule in AlertRule.objects.all()]})


@audited_admin_api('monitoring', 'create_alert_rule')
@api_view(['POST'])
def alert_rule_create(request):
    try:
        rule = create_alert_rule(request.data)
    except AlertRuleValidationError as error:
        return JsonResponse({'code': 400, 'message': str(error)}, status=400,
                            json_dumps_params={'ensure_ascii': False})
    except IntegrityError:
        return JsonResponse({'code': 400, 'message': '告警规则名称已存在'}, status=400,
                            json_dumps_params={'ensure_ascii': False})
    return JsonResponse({'code': 200, 'message': '告警规则已创建', 'item': serialize_alert_rule(rule)},
                        json_dumps_params={'ensure_ascii': False})


@audited_admin_api('monitoring', 'toggle_alert_rule')
@api_view(['POST'])
def alert_rule_toggle(request, rule_id):
    rule = get_object_or_404(AlertRule, id=rule_id)
    try:
        set_alert_rule_enabled(rule, request.data.get('enabled'))
    except AlertRuleValidationError as error:
        return JsonResponse({'code': 400, 'message': str(error)}, status=400,
                            json_dumps_params={'ensure_ascii': False})
    return JsonResponse({'code': 200, 'message': '告警规则状态已更新', 'item': serialize_alert_rule(rule)},
                        json_dumps_params={'ensure_ascii': False})
