"""Persisted inspection snapshots for API responses and offline downloads."""


def serialize_plan(plan):
    """Expose the validated plan contract without installation paths."""
    return {field: getattr(plan, field) for field in (
        'id', 'name', 'template_id', 'version', 'parameters', 'schedule_kind',
        'schedule_settings', 'timezone', 'enabled', 'revision', 'actor',
        'next_run', 'cursor', 'created_at', 'updated_at',
    )}