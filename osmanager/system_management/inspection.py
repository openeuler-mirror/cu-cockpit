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
    token = _ITEM_DEADLINE.set(min(deadline, started + INSPECTION_TEMPLATE['item_timeout']))
    try:
        result = dict(collector())
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
