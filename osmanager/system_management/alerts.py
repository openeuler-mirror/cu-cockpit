ALERT_METRICS = {'cpu_percent', 'memory_percent', 'root_percent', 'inode_percent'}
ALERT_OPERATORS = {'gte', 'lte'}


class AlertRuleValidationError(ValueError):
    pass


def normalize_alert_rule(payload):
    try:
        rule = {
            'name': str(payload.get('name') or '').strip(),
            'metric': str(payload.get('metric') or '').strip(),
            'operator': str(payload.get('operator') or 'gte').strip().lower(),
            'threshold': float(payload.get('threshold')),
            'recovery_threshold': float(payload.get('recovery_threshold')),
            'consecutive_hits': int(payload.get('consecutive_hits', 3)),
            'enabled': payload.get('enabled', True),
        }
    except (TypeError, ValueError) as error:
        raise AlertRuleValidationError('告警规则数值格式无效') from error
    valid = (
        0 < len(rule['name']) <= 128 and rule['metric'] in ALERT_METRICS
        and rule['operator'] in ALERT_OPERATORS
        and 0 <= rule['threshold'] <= 100 and 0 <= rule['recovery_threshold'] <= 100
        and 1 <= rule['consecutive_hits'] <= 60 and isinstance(rule['enabled'], bool)
    )
    if not valid:
        raise AlertRuleValidationError('告警规则字段或范围无效')
    if rule['operator'] == 'gte' and rule['recovery_threshold'] >= rule['threshold']:
        raise AlertRuleValidationError('高阈值告警的恢复阈值必须低于触发阈值')
    if rule['operator'] == 'lte' and rule['recovery_threshold'] <= rule['threshold']:
        raise AlertRuleValidationError('低阈值告警的恢复阈值必须高于触发阈值')
    return rule


def create_alert_rule(payload):
    from .models import AlertRule
    return AlertRule.objects.create(**normalize_alert_rule(payload))


def threshold_triggered(rule, value):
    if value is None:
        return False
    if rule.operator == 'gte':
        return value >= rule.threshold
    return value <= rule.threshold


def threshold_recovered(rule, value):
    if value is None:
        return False
    if rule.operator == 'gte':
        return value <= rule.recovery_threshold
    return value >= rule.recovery_threshold


def recent_rule_values(rule):
    if rule.metric not in ALERT_METRICS:
        raise AlertRuleValidationError('告警指标不在允许列表')
    from .models import MetricSample
    queryset = MetricSample.objects.exclude(**{f'{rule.metric}__isnull': True})
    return list(queryset.values_list(rule.metric, flat=True)[:rule.consecutive_hits])


def consecutive_triggered(rule, values):
    return len(values) >= rule.consecutive_hits and all(
        threshold_triggered(rule, value) for value in values[:rule.consecutive_hits]
    )


def consecutive_recovered(rule, values):
    return len(values) >= rule.consecutive_hits and all(
        threshold_recovered(rule, value) for value in values[:rule.consecutive_hits]
    )


def open_alert_event(rule, sample, values):
    from .models import AlertEvent
    current = getattr(sample, rule.metric)
    return AlertEvent.objects.get_or_create(
        rule=rule,
        status='active',
        defaults={
            'trigger_value': current,
            'last_value': current,
            'context': {'sample_id': sample.id, 'values': list(values)},
        },
    )


def recover_alert_event(event, value):
    from django.utils import timezone
    event.status = 'recovered'
    event.recovered_at = timezone.now()
    event.recovery_value = value
    event.last_value = value
    event.save(update_fields=['status', 'recovered_at', 'recovery_value', 'last_value'])
    return event


def update_alert_event_value(event, value):
    event.last_value = value
    event.save(update_fields=['last_value'])
    return event


def evaluate_alert_rule(rule, sample):
    value = getattr(sample, rule.metric)
    if not rule.enabled or value is None:
        return None
    from .models import AlertEvent
    active = AlertEvent.objects.filter(rule=rule, status='active').first()
    if active:
        values = recent_rule_values(rule)
        if consecutive_recovered(rule, values):
            return recover_alert_event(active, value)
        return update_alert_event_value(active, value)
    values = recent_rule_values(rule)
    if not consecutive_triggered(rule, values):
        return None
    event, _created = open_alert_event(rule, sample, values)
    return event


def evaluate_alert_rules(sample):
    from .models import AlertRule
    events = []
    for rule in AlertRule.objects.filter(enabled=True):
        event = evaluate_alert_rule(rule, sample)
        if event is not None:
            events.append(event)
    return events


def acknowledge_alert_event(event, actor):
    if event.status != 'active':
        raise AlertRuleValidationError('只能确认活动告警')
    from django.utils import timezone
    event.acknowledged_by = str(actor)
    event.acknowledged_at = timezone.now()
    event.save(update_fields=['acknowledged_by', 'acknowledged_at'])
    return event


def build_alert_context(event):
    from datetime import timedelta
    from django.utils import timezone
    from .ai_tools import execute_log_query
    from .models import MetricSample, OperationAudit
    since = event.started_at - timedelta(minutes=30)
    until = event.recovered_at or timezone.now()
    samples = list(MetricSample.objects.filter(collected_at__gte=since, collected_at__lte=until).values(
        'collected_at', 'cpu_percent', 'memory_percent', 'root_percent', 'inode_percent',
        'network_rx_bytes', 'network_tx_bytes', 'services',
    )[:120])
    audits = list(OperationAudit.objects.filter(created_at__gte=since, created_at__lte=until).values(
        'created_at', 'actor', 'module', 'action', 'target', 'success', 'message',
    )[:50])
    samples.reverse()
    audits.reverse()
    try:
        logs = execute_log_query({
            'priority': 'err', 'service': '', 'limit': 50,
            'since': since, 'until': until,
        })['logs']
    except RuntimeError:
        logs = []
    return {
        'alert': {
            'id': event.id, 'rule': event.rule.name, 'metric': event.rule.metric,
            'started_at': event.started_at, 'trigger_value': event.trigger_value,
            'last_value': event.last_value, 'status': event.status,
        },
        'samples': samples,
        'services': samples[-1]['services'] if samples else {},
        'audits': audits,
        'logs': logs,
    }


def analyze_alert_event(event):
    import json
    from .ai_analysis import analyze_context
    context = json.dumps(build_alert_context(event), ensure_ascii=False, default=str)
    return analyze_context('alert_context', context)


def set_alert_rule_enabled(rule, enabled):
    if not isinstance(enabled, bool):
        raise AlertRuleValidationError('enabled 必须为布尔值')
    rule.enabled = enabled
    rule.save(update_fields=['enabled', 'updated_at'])
    return rule


def serialize_alert_rule(rule):
    return {
        'id': rule.id,
        'name': rule.name,
        'metric': rule.metric,
        'operator': rule.operator,
        'threshold': rule.threshold,
        'recovery_threshold': rule.recovery_threshold,
        'consecutive_hits': rule.consecutive_hits,
        'enabled': rule.enabled,
        'created_at': rule.created_at,
        'updated_at': rule.updated_at,
    }


def serialize_alert_event(event):
    return {
        'id': event.id,
        'rule': {'id': event.rule_id, 'name': event.rule.name, 'metric': event.rule.metric},
        'status': event.status,
        'started_at': event.started_at,
        'recovered_at': event.recovered_at,
        'trigger_value': event.trigger_value,
        'last_value': event.last_value,
        'recovery_value': event.recovery_value,
        'acknowledged_by': event.acknowledged_by,
        'acknowledged_at': event.acknowledged_at,
        'context': event.context,
    }
