"""Versioned offline host inspection, without persistence or alert side effects."""

from types import MappingProxyType


INSPECTION_TEMPLATE = MappingProxyType({
    'id': 'local-host',
    'version': 'v1',
    'items': ('cpu', 'memory', 'root_capacity', 'root_inodes', 'time_sync'),
    'default_services': ('cu-cockpit.service',),
    'registered_services': (
        'cu-cockpit.service', 'crond.service', 'cron.service', 'chronyd.service',
        'systemd-timesyncd.service', 'sshd.service', 'ssh.service', 'nginx.service',
        'firewalld.service', 'NetworkManager.service', 'rsyslog.service',
        'auditd.service', 'dbus.service', 'systemd-journald.service',
        'systemd-logind.service', 'systemd-udevd.service',
    ),
    'max_services': 16,
    'warning': 80,
    'fail': 90,
    'item_timeout': 5,
    'run_timeout': 60,
})


def normalize_parameters(parameters=None):
    """Return immutable, registered service selections or reject unsafe input."""
    if parameters is None:
        parameters = {}
    if not isinstance(parameters, dict) or set(parameters) - {'services'}:
        raise ValueError('Only inspection services may be configured')
    services = parameters.get('services', INSPECTION_TEMPLATE['default_services'])
    if not isinstance(services, (list, tuple)):
        raise ValueError('Services must be a list of registered unit names')
    if len(services) > INSPECTION_TEMPLATE['max_services']:
        raise ValueError('At most 16 services may be inspected')
    if any(not isinstance(service, str) or
           service not in INSPECTION_TEMPLATE['registered_services'] for service in services):
        raise ValueError('Service unit is not registered')
    if len(set(services)) != len(services):
        raise ValueError('Duplicate service units are not allowed')
    return tuple(services)


def _run_item(item_id, label, collector, deadline):
    """Attach stable item metadata while binding an isolated command budget."""
    import time
    from .inspection_collectors import _ITEM_DEADLINE

    started = time.monotonic()
    if started >= deadline:
        return {
            'id': item_id, 'label': label, 'status': 'skipped', 'value': None,
            'unit': None, 'threshold': None, 'evidence': {'deadline_exhausted': True},
            'reason': 'Inspection run deadline exhausted; collector not started',
            'duration': 0.0, 'version': INSPECTION_TEMPLATE['version'],
        }
    token = _ITEM_DEADLINE.set(min(deadline, started + INSPECTION_TEMPLATE['item_timeout']))
    try:
        result = dict(collector())
        if time.monotonic() >= _ITEM_DEADLINE.get():
            raise TimeoutError('Inspection item deadline exceeded (5s maximum)')
    except Exception as error:
        result = {
            'status': 'error', 'value': None, 'unit': None, 'threshold': None,
            'evidence': {'error': type(error).__name__,
                         'output': str(getattr(error, 'output', '') or '')[:16384]},
            'reason': str(error)[:16384] or type(error).__name__,
        }
    finally:
        _ITEM_DEADLINE.reset(token)
    return {
        **result, 'id': item_id, 'label': label,
        'duration': time.monotonic() - started, 'version': INSPECTION_TEMPLATE['version'],
    }


def _overall_status(items, required=INSPECTION_TEMPLATE['items']):
    """Reduce completed health states without conflating them with job phases."""
    item_ids = [item.get('id') for item in items]
    if set(required) - set(item_ids) or len(item_ids) != len(set(item_ids)):
        return 'error'
    statuses = {item.get('status') for item in items}
    if statuses - {'error', 'fail', 'warning', 'pass', 'skipped'}:
        return 'error'
    if statuses == {'skipped'}:
        return 'skipped'
    if 'skipped' in statuses:
        return 'error'
    for status in ('error', 'fail', 'warning', 'pass'):
        if status in statuses:
            return status
    return 'error'
