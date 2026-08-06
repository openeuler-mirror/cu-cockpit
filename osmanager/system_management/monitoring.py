import re
from pathlib import Path

from .command import run_safe


class MetricCollectionError(RuntimeError):
    pass


def collect_cpu_percent():
    result = run_safe(['top', '-bn1'], {'top'}, timeout=5)
    match = re.search(r'([0-9]+(?:\.[0-9]+)?)\s*id\b', result.stdout)
    if not result.success or not match:
        raise MetricCollectionError('无法采集 CPU 使用率')
    return round(max(0.0, min(100.0, 100.0 - float(match.group(1)))), 2)


def collect_memory_percent(path=Path('/proc/meminfo')):
    try:
        values = {
            line.split(':', 1)[0]: int(line.split()[1])
            for line in path.read_text(encoding='utf-8').splitlines() if ':' in line
        }
        total = values['MemTotal']
        available = values['MemAvailable']
    except (OSError, KeyError, ValueError, IndexError) as error:
        raise MetricCollectionError('无法采集内存使用率') from error
    return round(max(0.0, min(100.0, (total - available) * 100.0 / total)), 2)


def parse_df_percent(output):
    lines = [line for line in str(output).splitlines() if line.strip()]
    if len(lines) < 2:
        raise MetricCollectionError('df 返回格式无效')
    match = re.search(r'([0-9]+)%', lines[-1])
    if not match:
        raise MetricCollectionError('df 返回格式无效')
    return float(match.group(1))
