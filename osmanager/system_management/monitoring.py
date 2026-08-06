import re

from .command import run_safe


class MetricCollectionError(RuntimeError):
    pass


def collect_cpu_percent():
    result = run_safe(['top', '-bn1'], {'top'}, timeout=5)
    match = re.search(r'([0-9]+(?:\.[0-9]+)?)\s*id\b', result.stdout)
    if not result.success or not match:
        raise MetricCollectionError('无法采集 CPU 使用率')
    return round(max(0.0, min(100.0, 100.0 - float(match.group(1)))), 2)
