"""Persistent single-host inspection jobs, without HTTP or systemd side effects."""

import fcntl
import os
from contextlib import contextmanager
from pathlib import Path

from django.conf import settings


@contextmanager
def inspection_lock():
    """Exclude other manual and timer workers using an inspection-only lock."""
    root = Path(getattr(settings, 'INSPECTION_STATE_DIR', settings.BASE_DIR / '.inspection'))
    root.mkdir(mode=0o700, exist_ok=True)
    directory = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        import stat

        metadata = os.fstat(directory)
        if metadata.st_uid != os.geteuid() or stat.S_IMODE(metadata.st_mode) != 0o700:
            raise PermissionError('Inspection state directory must be private and owned')
        descriptor = os.open('worker.lock', os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK,
                             0o600, dir_fd=directory)
        try:
            metadata = os.fstat(descriptor)
            if (not stat.S_ISREG(metadata.st_mode) or metadata.st_uid != os.geteuid() or
                    stat.S_IMODE(metadata.st_mode) != 0o600 or metadata.st_nlink != 1):
                raise PermissionError('Inspection lock must be a private owned regular file')
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            yield
        finally:
            os.close(descriptor)
    finally:
        os.close(directory)


def _run_values(actor, parameters=None, plan=None):
    """Freeze only validated v1 inputs into a new run's independent snapshot."""
    from .inspection_schedules import normalize_plan

    fields = ('name', 'template_id', 'version', 'parameters', 'schedule_kind',
              'enabled', 'timezone', 'schedule_settings')
    data = ({field: getattr(plan, field) for field in fields} if plan is not None
            else {'name': 'Manual inspection', 'parameters': parameters})
    values = normalize_plan(data, actor)
    return {
        'actor': actor, 'template_id': values['template_id'], 'version': values['version'],
        'parameters': values['parameters'],
        'plan_snapshot': ({'id': plan.pk, 'revision': plan.revision,
                           'name': values['name'], 'schedule_kind': values['schedule_kind'],
                           'timezone': values['timezone'],
                           'schedule_settings': values['schedule_settings']}
                          if plan is not None else {}),
    }


def queue_run(actor, *, parameters=None, plan_id=None):
    """Queue manual work after caller authorization, never collect in the request."""
    from django.db import transaction
    from django.db.models import F
    from .models import InspectionPlan, InspectionRun

    with transaction.atomic():
        InspectionRun.objects.filter(pk=0).update(actor=F('actor'))
        plan = (InspectionPlan.objects.get(pk=plan_id, actor=actor)
                if plan_id is not None else None)
        values = _run_values(actor, parameters, plan)
        return InspectionRun.objects.create(plan=plan, trigger='manual', **values)