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


def normalize_plan(data, actor):
    """Normalize the complete editable plan contract before any database write."""
    from .inspection import normalize_parameters

    allowed = {'name', 'template_id', 'version', 'parameters', 'schedule_kind',
               'enabled', 'timezone', 'schedule_settings'}
    if not isinstance(data, dict) or set(data) - allowed:
        raise ValueError('Unknown inspection plan fields')
    name = data.get('name')
    if (not isinstance(name, str) or not name.strip() or len(name) > 128 or
            not name.isprintable()):
        raise ValueError('Inspection name must contain 1 to 128 printable characters')
    if not isinstance(actor, str) or not actor.strip() or len(actor) > 150:
        raise ValueError('Inspection actor is required')
    if data.get('template_id', 'local-host') != 'local-host' or data.get('version', 'v1') != 'v1':
        raise ValueError('Only the built-in local-host v1 template is supported')
    enabled = data.get('enabled', False)
    if type(enabled) is not bool:
        raise ValueError('Enabled must be a boolean')
    kind = data.get('schedule_kind', 'manual')
    zone = data.get('timezone', 'Asia/Shanghai')
    options = normalize_schedule(kind, data.get('schedule_settings', {}), zone)
    return {
        'name': name.strip(), 'actor': actor, 'template_id': 'local-host', 'version': 'v1',
        'parameters': {'services': list(normalize_parameters(data.get('parameters')))},
        'schedule_kind': kind, 'schedule_settings': options, 'timezone': zone,
        'enabled': enabled,
    }