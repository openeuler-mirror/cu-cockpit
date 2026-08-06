ALERT_METRICS = {'cpu_percent', 'memory_percent', 'root_percent', 'inode_percent'}
ALERT_OPERATORS = {'gte', 'lte'}


class AlertRuleValidationError(ValueError):
    pass


def normalize_alert_rule(payload):
    return {
        'name': str(payload.get('name') or '').strip(),
        'metric': str(payload.get('metric') or '').strip(),
        'operator': str(payload.get('operator') or 'gte').strip().lower(),
        'threshold': float(payload.get('threshold')),
        'recovery_threshold': float(payload.get('recovery_threshold')),
        'consecutive_hits': int(payload.get('consecutive_hits', 3)),
        'enabled': payload.get('enabled', True),
    }
