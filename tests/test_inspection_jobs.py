"""Persistent inspection worker regressions with isolated Django databases."""

import tempfile
from datetime import datetime, timezone

from django.test import TestCase, override_settings


class InspectionJobsTest(TestCase):
    """Use the real project app and migrations without host collection."""

    def setUp(self):
        self.lock_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.lock_directory.cleanup)
        self.settings_override = override_settings(INSPECTION_STATE_DIR=self.lock_directory.name)
        self.settings_override.enable()
        self.addCleanup(self.settings_override.disable)
        self.now = datetime(2026, 10, 29, tzinfo=timezone.utc)

    def _plan(self, **overrides):
        from osmanager.system_management.inspection_schedules import save_plan

        return save_plan({
            'name': 'Host inspection', 'enabled': True, 'timezone': 'UTC',
            'schedule_kind': 'interval', 'schedule_settings': {'minutes': 15},
            'parameters': {'services': ['nginx.service']}, **overrides,
        }, 'operator', now=self.now)

    def _result(self):
        from unittest.mock import patch
        from osmanager.system_management import inspection, inspection_collectors

        metric = inspection_collectors.percent_result(10, {'observed_percent': 10})
        synchronized = {
            'status': 'pass', 'value': True, 'unit': None,
            'threshold': {'NTPSynchronized': 'yes'}, 'reason': 'NTPSynchronized=yes',
            'evidence': {'properties': {'NTPSynchronized': 'yes'}, 'returncode': 0,
                         'output': 'NTPSynchronized=yes\n', 'command': [
                             'timedatectl', 'show', '--no-pager',
                             '--property=NTPSynchronized,NTP,CanNTP']},
        }
        states = {'LoadState': 'loaded', 'ActiveState': 'active',
                  'SubState': 'running', 'Result': 'success'}
        service = {
            'status': 'pass', 'value': states, 'unit': None,
            'threshold': {**states, 'SubState': ['running', 'exited']},
            'reason': 'nginx.service: ActiveState=active',
            'evidence': {'properties': states, 'returncode': 0,
                         'output': ''.join(f'{key}={value}\n' for key, value in states.items()),
                         'command': ['systemctl', 'show', '--no-pager',
                                     '--property=LoadState,ActiveState,SubState,Result',
                                     '--', 'nginx.service']},
        }
        with patch.object(inspection_collectors, '_collect_metric', return_value=metric), \
                patch.object(inspection_collectors, 'collect_time_sync', return_value=synchronized), \
                patch.object(inspection_collectors, 'collect_services', return_value=[service]), \
                patch('time.monotonic', return_value=10):
            return inspection.run_inspection({'services': ['nginx.service']})

    def test_run_persists_complete_success_and_snapshots(self):
        from unittest.mock import patch
        from osmanager.system_management import inspection_jobs as jobs

        plan = self._plan()
        queued = jobs.queue_run('operator', plan_id=plan.pk)
        expected = self._result()
        with patch('osmanager.system_management.inspection.run_inspection',
                   return_value=expected) as collect:
            completed = jobs.run_next(now=self.now)
        collect.assert_called_once_with({'services': ['nginx.service']})
        queued.refresh_from_db()
        self.assertEqual(completed.pk, queued.pk)
        self.assertEqual((queued.phase, queued.health, queued.error), ('finished', 'pass', ''))
        self.assertEqual((queued.template_id, queued.version), ('local-host', 'v1'))
        self.assertEqual(queued.parameters, expected['parameters'])
        self.assertEqual(queued.plan_snapshot, {
            'id': plan.pk, 'revision': 1, 'name': 'Host inspection',
            'schedule_kind': 'interval', 'timezone': 'UTC',
            'schedule_settings': {'minutes': 15},
        })
        self.assertEqual(queued.items, expected['items'])
        self.assertEqual(len(queued.items), 6)
        self.assertEqual(queued.duration, expected['duration'])
        self.assertEqual(queued.started_at, self.now)
        self.assertIsNotNone(queued.finished_at)

    def test_core_exception_is_persisted_as_error_without_retry(self):
        from unittest.mock import patch
        from osmanager.system_management import inspection_jobs as jobs

        queued = jobs.queue_run('operator', parameters={'services': ['nginx.service']})
        with patch('osmanager.system_management.inspection.run_inspection',
                   side_effect=RuntimeError('collector failed')) as collect:
            failed = jobs.run_next(now=self.now)
            self.assertIsNone(jobs.run_next(now=self.now))
        collect.assert_called_once_with({'services': ['nginx.service']})
        queued.refresh_from_db()
        self.assertEqual(failed.pk, queued.pk)
        self.assertEqual((queued.phase, queued.health), ('finished', 'error'))
        self.assertEqual(queued.error, 'RuntimeError: collector failed')
        self.assertEqual(queued.items, [])
        self.assertGreaterEqual(queued.duration, 0)
        self.assertEqual(queued.started_at, self.now)
        self.assertIsNotNone(queued.finished_at)

    def test_due_slot_is_unique_and_idempotent_after_reload(self):
        import importlib
        from django.db import IntegrityError, transaction
        from osmanager.system_management import inspection_jobs as jobs
        from osmanager.system_management.models import InspectionPlan, InspectionRun

        plan = self._plan()
        slot = plan.next_run
        queued, = jobs.queue_due(now=slot)
        self.assertEqual((queued.trigger, queued.scheduled_slot), ('scheduled', slot))
        self.assertEqual(jobs.queue_due(now=slot), [])
        InspectionRun.objects.filter(pk=queued.pk).update(
            phase='finished', health='pass', finished_at=slot)
        InspectionPlan.objects.filter(pk=plan.pk).update(next_run=slot)
        restarted = importlib.reload(jobs)
        self.assertEqual(restarted.queue_due(now=slot), [])
        self.assertEqual(InspectionRun.objects.filter(plan=plan, scheduled_slot=slot).count(), 1)
        plan.refresh_from_db()
        self.assertEqual(plan.cursor, slot)
        self.assertGreater(plan.next_run, slot)
        with self.assertRaises(IntegrityError), transaction.atomic():
            InspectionRun.objects.create(
                plan=plan, scheduled_slot=slot, trigger='scheduled', actor='operator',
                template_id='local-host', version='v1', phase='finished')

    def test_disabled_plan_never_queues_even_with_stale_due_slot(self):
        from osmanager.system_management import inspection_jobs as jobs
        from osmanager.system_management.models import InspectionPlan, InspectionRun

        plan = self._plan(enabled=False)
        self.assertIsNone(plan.next_run)
        InspectionPlan.objects.filter(pk=plan.pk).update(next_run=self.now)
        self.assertEqual(jobs.queue_due(now=self.now), [])
        self.assertEqual(InspectionRun.objects.count(), 0)
        plan.refresh_from_db()
        self.assertIsNone(plan.cursor)
        self.assertFalse(plan.enabled)

    def test_plan_triggers_deduplicate_queued_and_running_work(self):
        from osmanager.system_management import inspection_jobs as jobs
        from osmanager.system_management.models import InspectionRun

        plan = self._plan()
        queued = jobs.queue_run('operator', plan_id=plan.pk)
        self.assertEqual(jobs.queue_run('operator', plan_id=plan.pk).pk, queued.pk)
        with jobs.inspection_lock():
            claimed = jobs._claim_next(self.now)
        self.assertEqual(claimed.pk, queued.pk)
        active = jobs.queue_run('operator', plan_id=plan.pk)
        self.assertEqual((active.pk, active.phase), (queued.pk, 'running'))
        self.assertEqual(InspectionRun.objects.filter(plan=plan).count(), 1)