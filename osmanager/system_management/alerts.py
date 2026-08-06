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
