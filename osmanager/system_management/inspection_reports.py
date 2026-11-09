"""Persisted inspection snapshots for API responses and offline downloads."""


def serialize_plan(plan):
    """Expose the validated plan contract without installation paths."""
    return {field: getattr(plan, field) for field in (
        'id', 'name', 'template_id', 'version', 'parameters', 'schedule_kind',
        'schedule_settings', 'timezone', 'enabled', 'revision', 'actor',
        'next_run', 'cursor', 'created_at', 'updated_at',
    )}


def serialize_run(run):
    """Keep job phase separate from persisted health and item evidence."""
    data = {field: getattr(run, field) for field in (
        'id', 'plan_id', 'plan_snapshot', 'trigger', 'actor', 'template_id', 'version',
        'parameters', 'phase', 'health', 'scheduled_slot', 'queued_at', 'started_at',
        'finished_at', 'duration', 'items', 'error',
    )}
    data['counts'] = {
        state: sum(item.get('status') == state for item in run.items)
        for state in ('pass', 'warning', 'fail', 'error', 'skipped')
    }
    data['error'] = 'Inspection did not complete successfully' if run.error else ''
    return data