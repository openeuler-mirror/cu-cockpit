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
