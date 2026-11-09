"""Validated inspection plan schedules, independent of cron and monitoring."""

from zoneinfo import ZoneInfo


def normalize_schedule(kind, options, timezone):
    """Accept only known schedule fields and an installed IANA timezone."""
    if not isinstance(timezone, str) or not timezone or len(timezone) > 64:
        raise ValueError('Invalid inspection timezone')
    ZoneInfo(timezone)
    if not isinstance(options, dict):
        raise ValueError('Schedule settings must be an object')
    if kind == 'daily':
        import re
        value = options.get('time')
        if (set(options) != {'time'} or not isinstance(value, str) or
                not re.fullmatch(r'(?:[01][0-9]|2[0-3]):[0-5][0-9]', value)):
            raise ValueError('Daily time must be HH:MM')
        return {'time': value}
    if kind != 'manual' or options:
        raise ValueError('Invalid inspection schedule')
    return {}