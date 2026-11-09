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