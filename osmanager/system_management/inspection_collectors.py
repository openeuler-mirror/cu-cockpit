"""Private fixed-command collectors for offline inspection."""

from .inspection import INSPECTION_TEMPLATE


def _validate_command(args):
    """Accept only exact built-in read-only query shapes."""
    command = tuple(args)
    fixed = (
        ('top', '-bn2', '-d0.2'),
        ('df', '-P', '--', '/'),
        ('df', '-Pi', '--', '/'),
        ('timedatectl', 'show', '--no-pager',
         '--property=NTPSynchronized,NTP,CanNTP'),
    )
    service_prefix = (
        'systemctl', 'show', '--no-pager',
        '--property=LoadState,ActiveState,SubState,Result', '--',
    )
    if command not in fixed and not (
            len(command) == 6 and command[:5] == service_prefix and
            command[5] in INSPECTION_TEMPLATE['registered_services']):
        raise ValueError('Command is not a built-in inspection query')
    return command
