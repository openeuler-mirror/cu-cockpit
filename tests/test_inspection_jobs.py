"""Persistent inspection worker regressions with isolated Django databases."""

import tempfile
from datetime import datetime, timezone

from django.test import TestCase, override_settings


class InspectionJobsTest(TestCase):
    """Use the real project app and migrations without host collection."""

    def test_worker_can_retry_failed_service_with_active_timer(self):
        from types import SimpleNamespace
        from unittest.mock import call, patch
        from osmanager.system_management.inspection_runtime import worker_status

        results = [SimpleNamespace(success=True, stdout=output) for output in (
            'LoadState=loaded\nActiveState=active\n',
            'LoadState=loaded\nActiveState=failed\n',
        )]
        with patch('osmanager.system_management.command.run_safe', side_effect=results) as run, \
                patch('pathlib.Path.is_file', return_value=True), \
                patch('os.access', return_value=True):
            status = worker_status()
        self.assertTrue(status['available'])
        self.assertIsNone(status['reason'])
        self.assertEqual(status['last_run_state'], 'failed')
        self.assertEqual(run.call_args_list, [call([
            'systemctl', 'show', '--no-pager', '--property=LoadState,ActiveState',
            '--', f'cu-cockpit-inspection.{kind}',
        ], allowed_commands={'systemctl'}, timeout=2, output_limit=4096)
            for kind in ('timer', 'service')])

    def setUp(self):
        self.lock_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.lock_directory.cleanup)
        self.settings_override = override_settings(INSPECTION_STATE_DIR=self.lock_directory.name)
        self.settings_override.enable()
        self.addCleanup(self.settings_override.disable)
        self.now = datetime(2026, 10, 29, tzinfo=timezone.utc)

    def test_worker_is_unavailable_when_timer_is_inactive(self):
        from types import SimpleNamespace
        from unittest.mock import patch
        from osmanager.system_management.inspection_runtime import worker_status

        for active_state in ('inactive', 'failed', 'deactivating', ''):
            with self.subTest(timer_state=active_state):
                results = [SimpleNamespace(success=True, stdout=output) for output in (
                    f'LoadState=loaded\nActiveState={active_state}\n',
                    'LoadState=loaded\nActiveState=failed\n',
                )]
                with patch('osmanager.system_management.command.run_safe', side_effect=results):
                    status = worker_status()
                self.assertFalse(status['available'])
                self.assertEqual(status['reason'], 'Inspection timer is not active')
                self.assertEqual(status['last_run_state'], 'failed')

    def _plan(self, **overrides):
        from osmanager.system_management.inspection_schedules import save_plan

        return save_plan({
            'name': 'Host inspection', 'enabled': True, 'timezone': 'UTC',
            'schedule_kind': 'interval', 'schedule_settings': {'minutes': 15},
            'parameters': {'services': ['nginx.service']}, **overrides,
        }, 'operator', now=self.now)

    def test_worker_is_unavailable_when_a_unit_is_missing(self):
        from types import SimpleNamespace
        from unittest.mock import patch
        from osmanager.system_management.inspection_runtime import worker_status

        for index, kind in enumerate(('timer', 'service')):
            for load_state in ('not-found', 'error', ''):
                with self.subTest(unit=kind, load_state=load_state):
                    results = [SimpleNamespace(success=True, stdout=output) for output in (
                        'LoadState=loaded\nActiveState=active\n',
                        'LoadState=loaded\nActiveState=failed\n',
                    )]
                    results[index].stdout = f'LoadState={load_state}\nActiveState=inactive\n'
                    with patch('osmanager.system_management.command.run_safe', side_effect=results):
                        status = worker_status()
                    self.assertFalse(status['available'])
                    self.assertEqual(status['reason'],
                                     f'Inspection {kind} unit is not loaded or installed')

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

    def test_plan_updates_preserve_queued_and_finished_snapshots(self):
        from copy import deepcopy
        from unittest.mock import patch
        from osmanager.system_management import inspection_jobs as jobs
        from osmanager.system_management.inspection_schedules import update_plan

        plan = self._plan()
        queued = jobs.queue_run('operator', plan_id=plan.pk)
        snapshot = deepcopy(queued.plan_snapshot)
        parameters = deepcopy(queued.parameters)
        updated = update_plan(plan.pk, {
            'name': 'Changed plan', 'parameters': {'services': ['sshd.service']},
            'enabled': True, 'schedule_kind': 'interval',
            'schedule_settings': {'minutes': 30}, 'timezone': 'Asia/Shanghai',
        }, 'operator', now=self.now)
        queued.refresh_from_db()
        self.assertEqual((queued.parameters, queued.plan_snapshot), (parameters, snapshot))
        self.assertEqual(updated.revision, 2)
        expected = self._result()
        with patch('osmanager.system_management.inspection.run_inspection',
                   return_value=expected) as collect:
            jobs.run_next(now=self.now)
        collect.assert_called_once_with(parameters)
        queued.refresh_from_db()
        self.assertEqual(queued.phase, 'finished')
        self.assertEqual((queued.parameters, queued.plan_snapshot), (parameters, snapshot))
        self.assertEqual((queued.template_id, queued.version), ('local-host', 'v1'))
        self.assertEqual(queued.items, expected['items'])

    def test_worker_reentry_is_rejected_before_claim_or_collection(self):
        from unittest.mock import patch
        from osmanager.system_management import inspection_jobs as jobs

        queued = jobs.queue_run('operator')
        with patch('osmanager.system_management.inspection.run_inspection') as collect:
            with jobs.inspection_lock():
                with self.assertRaises(BlockingIOError):
                    jobs.run_next(now=self.now)
        collect.assert_not_called()
        queued.refresh_from_db()
        self.assertEqual(queued.phase, 'queued')
        self.assertIsNone(queued.started_at)
        self.assertIsNone(queued.finished_at)
        self.assertIsNone(queued.health)

    def test_worker_flock_excludes_a_real_second_process(self):
        import subprocess
        import sys
        from osmanager.system_management import inspection_jobs as jobs

        queued = jobs.queue_run('operator')
        child = (
            "import os, sys\n"
            "os.environ['DJANGO_SETTINGS_MODULE'] = 'osmanager.settings'\n"
            "from django.conf import settings\n"
            "settings.DATABASES['default']['NAME'] = ':memory:'\n"
            "settings.INSPECTION_STATE_DIR = sys.argv[1]\n"
            "import django\ndjango.setup()\n"
            "from osmanager.system_management.inspection_jobs import run_next\n"
            "try:\n    run_next()\n"
            "except BlockingIOError:\n    sys.exit(23)\n"
            "sys.exit(24)\n"
        )
        with jobs.inspection_lock():
            process = subprocess.run(
                [sys.executable, '-c', child, self.lock_directory.name],
                capture_output=True, text=True, timeout=15, check=False)
        self.assertEqual(process.returncode, 23, process.stderr)
        queued.refresh_from_db()
        self.assertEqual(queued.phase, 'queued')
        self.assertIsNone(queued.started_at)

    def test_interrupted_running_work_is_failed_without_reexecution(self):
        from unittest.mock import patch
        from osmanager.system_management import inspection_jobs as jobs

        interrupted = jobs.queue_run('operator', parameters={'services': []})
        with jobs.inspection_lock():
            self.assertEqual(jobs._claim_next(self.now).pk, interrupted.pk)
        following = jobs.queue_run('operator', parameters={'services': ['nginx.service']})
        expected = self._result()
        with patch('osmanager.system_management.inspection.run_inspection',
                   return_value=expected) as collect:
            completed = jobs.run_next(now=self.now)
        collect.assert_called_once_with({'services': ['nginx.service']})
        self.assertEqual(completed.pk, following.pk)
        interrupted.refresh_from_db()
        self.assertEqual((interrupted.phase, interrupted.health), ('finished', 'error'))
        self.assertIn('interrupted', interrupted.error)
        self.assertIn('not retried', interrupted.error)
        self.assertEqual(interrupted.finished_at, self.now)
        self.assertEqual(interrupted.started_at, self.now)
        self.assertEqual(interrupted.items, [])
        following.refresh_from_db()
        self.assertEqual((following.phase, following.health), ('finished', 'pass'))

    def test_disabling_plan_skips_queued_scheduled_work(self):
        from unittest.mock import patch
        from osmanager.system_management import inspection_jobs as jobs
        from osmanager.system_management.inspection_schedules import set_plan_enabled

        plan = self._plan()
        slot = plan.next_run
        queued, = jobs.queue_due(now=slot)
        set_plan_enabled(plan.pk, False, 'operator', now=slot)
        with patch('osmanager.system_management.inspection.run_inspection') as collect:
            self.assertIsNone(jobs.run_next(now=slot))
        collect.assert_not_called()
        queued.refresh_from_db()
        self.assertEqual((queued.phase, queued.health), ('finished', 'skipped'))
        self.assertIsNone(queued.started_at)
        self.assertEqual(queued.finished_at, slot)
        self.assertIn('disabled', queued.error)
        self.assertEqual(queued.items, [])

    def test_failed_health_is_not_converted_to_success(self):
        from unittest.mock import patch
        from osmanager.system_management import inspection_jobs as jobs
        from osmanager.system_management.inspection import _overall_status

        queued = jobs.queue_run('operator', parameters={'services': ['nginx.service']})
        expected = self._result()
        expected['items'][0].update(
            status='fail', value=95, evidence={'observed_percent': 95},
            reason='Observed 95% meets failure threshold 90%')
        expected['status'] = _overall_status(expected['items'])
        self.assertEqual(expected['status'], 'fail')
        with patch('osmanager.system_management.inspection.run_inspection',
                   return_value=expected) as collect:
            completed = jobs.run_next(now=self.now)
        collect.assert_called_once_with(queued.parameters)
        queued.refresh_from_db()
        self.assertEqual((completed.health, queued.phase, queued.health),
                         ('fail', 'finished', 'fail'))
        self.assertEqual(queued.items, expected['items'])
        self.assertEqual(queued.items[0]['evidence'], {'observed_percent': 95})