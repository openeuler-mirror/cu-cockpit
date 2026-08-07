from datetime import timedelta

from django.http import JsonResponse
from django.utils import timezone
from rest_framework.decorators import api_view

from osmanager.auth.decorators import login_required_api

from .alerts import serialize_alert_rule
from .models import AlertRule, MetricSample
from .monitoring import serialize_metric_sample


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
