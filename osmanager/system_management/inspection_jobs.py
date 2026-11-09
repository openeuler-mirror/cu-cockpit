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

    if plan is not None and parameters is not None:
        raise ValueError('Plan parameters cannot be overridden when triggering a run')
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
        if plan is not None:
            active = InspectionRun.objects.filter(
                plan=plan, phase__in=['queued', 'running']).first()
            if active is not None:
                return active
        if InspectionRun.objects.filter(phase__in=['queued', 'running']).count() >= 64:
            raise ValueError('Inspection queue limit reached (64)')
        return InspectionRun.objects.create(plan=plan, trigger='manual', **values)


def queue_due(*, now=None):
    """Coalesce overdue slots; busy plans skip a slot, full queues retry later."""
    from django.db import transaction
    from django.db.models import F
    from django.utils import timezone
    from .inspection_schedules import next_slot
    from .models import InspectionPlan, InspectionRun

    now = now or timezone.now()
    queued = []
    with transaction.atomic():
        InspectionRun.objects.filter(pk=0).update(actor=F('actor'))
        plans = InspectionPlan.objects.filter(enabled=True, next_run__lte=now).order_by('id')[:64]
        for plan in plans:
            slot = plan.next_run
            previous = InspectionRun.objects.filter(plan=plan, scheduled_slot=slot).exists()
            busy = InspectionRun.objects.filter(plan=plan, phase__in=['queued', 'running']).exists()
            if not previous and not busy and (plan.cursor is None or slot > plan.cursor):
                if InspectionRun.objects.filter(phase__in=['queued', 'running']).count() >= 64:
                    break
                run = queue_run(plan.actor, plan_id=plan.pk)
                run.trigger = 'scheduled'
                run.scheduled_slot = slot
                run.save(update_fields=['trigger', 'scheduled_slot'])
                queued.append(run)
            plan.cursor = max(slot, plan.cursor or slot)
            plan.next_run = next_slot(plan, max(now, plan.cursor))
            plan.save(update_fields=['cursor', 'next_run'])
    return queued


def _claim_next(now):
    """Atomically claim the oldest queued run; caller must hold inspection_lock."""
    from django.db import transaction
    from django.db.models import F, Q
    from .models import InspectionRun

    with transaction.atomic():
        InspectionRun.objects.filter(pk=0).update(actor=F('actor'))
        InspectionRun.objects.filter(phase='running').update(
            phase='finished', health='error', finished_at=now,
            error='Inspection worker interrupted; run was not retried')
        InspectionRun.objects.filter(phase='queued', trigger='scheduled').filter(
            Q(plan__enabled=False) | Q(plan__isnull=True)).update(
                phase='finished', health='skipped', finished_at=now,
                error='Inspection plan is disabled or deleted')
        run = InspectionRun.objects.filter(phase='queued').order_by('queued_at', 'id').first()
        if run is None:
            return None
        claimed = InspectionRun.objects.filter(pk=run.pk, phase='queued').update(
            phase='running', started_at=now)
        if not claimed:
            return None
        run.phase = 'running'
        run.started_at = now
        return run