"""Availability of the fixed local inspection worker, not host health."""


def worker_status():
    """Check only installed unit availability without starting any unit."""
    from .command import run_safe

    units = {}
    for kind in ('timer', 'service'):
        try:
            result = run_safe([
                'systemctl', 'show', '--no-pager', '--property=LoadState,ActiveState',
                '--', f'cu-cockpit-inspection.{kind}',
            ], allowed_commands={'systemctl'}, timeout=2, output_limit=4096)
        except (OSError, ValueError, TimeoutError):
            return {'available': False, 'reason': 'Inspection worker status is unavailable',
                    'poll_seconds': 60, 'runs_per_trigger': 1}
        units[kind] = dict(line.split('=', 1) for line in result.stdout.splitlines()
                           if '=' in line) if result.success else {}
    available = (
        units['timer'].get('LoadState') == 'loaded' and
        units['timer'].get('ActiveState') == 'active' and
        units['service'].get('LoadState') == 'loaded' and
        units['service'].get('ActiveState') in ('inactive', 'active', 'activating')
    )
    return {'available': available, 'reason': None if available else
            'Inspection timer or service is not available', 'poll_seconds': 60,
            'runs_per_trigger': 1}