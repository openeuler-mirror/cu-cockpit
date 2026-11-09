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
    if kind == 'interval':
        value = options.get('minutes')
        if set(options) != {'minutes'} or type(value) is not int or value not in (15, 30, 60):
            raise ValueError('Interval minutes must be 15, 30 or 60')
        return {'minutes': value}
    if kind != 'manual' or options:
        raise ValueError('Invalid inspection schedule')
    return {}


def next_slot(plan, after):
    """Return the next UTC-aligned interval strictly after an aware instant."""
    from datetime import datetime, timezone

    if after.utcoffset() is None:
        raise ValueError('Schedule instants must be timezone aware')
    options = normalize_schedule(plan.schedule_kind, plan.schedule_settings, plan.timezone)
    if not plan.enabled or plan.schedule_kind == 'manual':
        return None
    if plan.schedule_kind == 'interval':
        seconds = options['minutes'] * 60
        return datetime.fromtimestamp((after.timestamp() // seconds + 1) * seconds, timezone.utc)
    from datetime import timedelta

    zone = ZoneInfo(plan.timezone)
    local = after.astimezone(zone)
    hour, minute = map(int, options['time'].split(':'))
    for offset in range(3):
        wall = (local + timedelta(days=offset)).replace(
            hour=hour, minute=minute, second=0, microsecond=0, tzinfo=None)
        candidate = wall.replace(tzinfo=zone, fold=0).astimezone(timezone.utc)
        if (candidate > after and
                candidate.astimezone(zone).replace(tzinfo=None) == wall):
            return candidate
    raise ValueError('No valid daily inspection slot')