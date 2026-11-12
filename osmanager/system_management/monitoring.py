import re
from pathlib import Path

from .command import run_safe


MONITORED_SERVICES = ('cu-cockpit', 'crond', 'chronyd', 'firewalld')


class MetricCollectionError(RuntimeError):
    pass


def collect_cpu_percent(runner=None):
    import math

    result = (runner or run_safe)(['top', '-bn1'], {'top'}, timeout=5)
    match = re.search(
        r'(?:^|[\s,])([+-]?(?:(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)'
        r'(?:[eE][+-]?[0-9]+)?|nan|inf(?:inity)?))\s*id\b',
        result.stdout, re.IGNORECASE,
    )
    if not result.success or not match:
        raise MetricCollectionError('无法采集 CPU 使用率')
    idle = float(match.group(1))
    if not math.isfinite(idle) or not 0 <= idle <= 100:
        raise MetricCollectionError('无法采集 CPU 使用率')
    return round(max(0.0, min(100.0, 100.0 - idle)), 2)


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


def collect_root_percent(runner=None):
    result = (runner or run_safe)(['df', '-P', '--', '/'], {'df'}, timeout=5)
    if not result.success:
        raise MetricCollectionError('无法采集根文件系统使用率')
    return parse_df_percent(result.stdout)


def collect_inode_percent(runner=None):
    result = (runner or run_safe)(['df', '-Pi', '--', '/'], {'df'}, timeout=5)
    if not result.success:
        raise MetricCollectionError('无法采集根 inode 使用率')
    return parse_df_percent(result.stdout)


def collect_network_bytes(path=Path('/proc/net/dev')):
    received = transmitted = 0
    try:
        for line in path.read_text(encoding='utf-8').splitlines():
            if ':' not in line:
                continue
            interface, values = line.split(':', 1)
            fields = values.split()
            if interface.strip() != 'lo' and len(fields) >= 9:
                received += int(fields[0])
                transmitted += int(fields[8])
    except (OSError, ValueError) as error:
        raise MetricCollectionError('无法采集网络流量') from error
    return {'network_rx_bytes': received, 'network_tx_bytes': transmitted}


def collect_service_states(services=MONITORED_SERVICES):
    states = {}
    for service in services:
        try:
            result = run_safe(['systemctl', 'is-active', service], {'systemctl'}, timeout=3)
            states[service] = result.stdout.strip() or ('inactive' if result.returncode else 'active')
        except (OSError, RuntimeError):
            states[service] = 'unknown'
    return states


def collect_metric_values():
    values = {}
    collectors = (
        ('cpu_percent', collect_cpu_percent),
        ('memory_percent', collect_memory_percent),
        ('root_percent', collect_root_percent),
        ('inode_percent', collect_inode_percent),
    )
    for field, collector in collectors:
        try:
            values[field] = collector()
        except MetricCollectionError:
            values[field] = None
    try:
        values.update(collect_network_bytes())
    except MetricCollectionError:
        values.update(network_rx_bytes=None, network_tx_bytes=None)
    values['services'] = collect_service_states()
    return values


def collect_metric_sample():
    from .models import MetricSample
    from .alerts import evaluate_alert_rules
    sample = MetricSample.objects.create(**collect_metric_values())
    evaluate_alert_rules(sample)
    return sample


def purge_metric_samples(retention_days=30):
    days = int(retention_days)
    if not 1 <= days <= 365:
        raise ValueError('指标保留天数范围为 1-365')
    from datetime import timedelta
    from django.utils import timezone
    from .models import MetricSample
    deleted, _ = MetricSample.objects.filter(collected_at__lt=timezone.now() - timedelta(days=days)).delete()
    return deleted


def serialize_metric_sample(sample):
    return {
        'id': sample.id,
        'collected_at': sample.collected_at,
        'cpu_percent': sample.cpu_percent,
        'memory_percent': sample.memory_percent,
        'root_percent': sample.root_percent,
        'inode_percent': sample.inode_percent,
        'network_rx_bytes': sample.network_rx_bytes,
        'network_tx_bytes': sample.network_tx_bytes,
        'services': sample.services,
    }
