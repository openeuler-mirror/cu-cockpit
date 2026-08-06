ALERT_METRICS = {'cpu_percent', 'memory_percent', 'root_percent', 'inode_percent'}
ALERT_OPERATORS = {'gte', 'lte'}


class AlertRuleValidationError(ValueError):
    pass
