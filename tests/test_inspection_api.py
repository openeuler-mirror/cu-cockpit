"""Inspection HTTP contracts through the production URL configuration."""

import tempfile
from types import SimpleNamespace
from unittest.mock import patch

from django.test import Client, TestCase, override_settings


class InspectionAPITest(TestCase):
    """Keep authentication, CSRF, persistence and report rendering real."""

    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)
        self.base = '/api/system/inspection'
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.enterContext(override_settings(INSPECTION_STATE_DIR=directory.name))
        self.account = self.enterContext(patch(
            'osmanager.system_management.permissions.pwd.getpwnam',
            return_value=SimpleNamespace(pw_uid=0)))
        self.collect = self.enterContext(patch(
            'osmanager.system_management.inspection.run_inspection',
            side_effect=AssertionError('HTTP must not run inspections')))
        self.probe = self.enterContext(patch(
            'osmanager.system_management.inspection_collectors._run_readonly',
            side_effect=AssertionError('HTTP must not probe the host')))
        self.metric = self.enterContext(patch(
            'osmanager.system_management.inspection_collectors._collect_metric',
            side_effect=AssertionError('HTTP must not collect metrics')))

    def _login(self, username='operator', uid=0):
        self.account.return_value = SimpleNamespace(pw_uid=uid)
        session = self.client.session
        session['username'] = username
        session.save()
        response = self.client.get(f'{self.base}/overview')
        self.assertEqual(response.status_code, 200)
        self.assertIn('csrftoken', response.cookies)
        return self.client.cookies['csrftoken'].value

    def test_anonymous_overview_is_unauthorized_without_probes(self):
        with patch('osmanager.system_management.inspection_runtime.worker_status') as worker:
            response = self.client.get(f'{self.base}/overview')
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['code'], 401)
        worker.assert_not_called()
        self.account.assert_not_called()
        self.collect.assert_not_called()
        self.probe.assert_not_called()
        self.metric.assert_not_called()

    def _plan(self, actor='operator'):
        from osmanager.system_management.inspection_schedules import save_plan

        return save_plan({
            'name': 'Host inspection', 'enabled': True, 'timezone': 'UTC',
            'schedule_kind': 'interval', 'schedule_settings': {'minutes': 15},
            'parameters': {'services': ['nginx.service']},
        }, actor)

    def test_viewer_cannot_toggle_plan_or_change_inspection_rows(self):
        from osmanager.system_management.models import InspectionPlan, InspectionRun

        plan = self._plan(actor='viewer')
        token = self._login('viewer', uid=1000)
        before = list(InspectionPlan.objects.values())
        response = self.client.post(
            f'{self.base}/plans/{plan.pk}/toggle', {'enabled': False},
            content_type='application/json', HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()['code'], 403)
        self.account.assert_called_with('viewer')
        self.assertEqual(list(InspectionPlan.objects.values()), before)
        self.assertEqual(InspectionRun.objects.count(), 0)
        self.collect.assert_not_called()
        self.probe.assert_not_called()
        self.metric.assert_not_called()

    def test_admin_post_without_csrf_token_is_rejected(self):
        from osmanager.system_management.models import InspectionPlan, InspectionRun

        plan = self._plan()
        self._login()
        self.account.reset_mock()
        before = list(InspectionPlan.objects.values())
        response = self.client.post(
            f'{self.base}/run', {'plan_id': plan.pk}, content_type='application/json')
        self.assertEqual(response.status_code, 403)
        self.assertIn(b'CSRF', response.content)
        self.account.assert_not_called()
        self.assertEqual(list(InspectionPlan.objects.values()), before)
        self.assertEqual(InspectionRun.objects.count(), 0)
        self.collect.assert_not_called()
        self.probe.assert_not_called()
        self.metric.assert_not_called()

    def test_viewer_cannot_create_plan_or_change_inspection_rows(self):
        from osmanager.system_management.models import InspectionPlan, InspectionRun

        self._plan()
        token = self._login('viewer', uid=1000)
        before = list(InspectionPlan.objects.values())
        response = self.client.post(
            f'{self.base}/plans/create', {'name': 'Forbidden plan'},
            content_type='application/json', HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()['code'], 403)
        self.account.assert_called_with('viewer')
        self.assertEqual(list(InspectionPlan.objects.values()), before)
        self.assertEqual(InspectionRun.objects.count(), 0)
        self.collect.assert_not_called()
        self.probe.assert_not_called()
        self.metric.assert_not_called()

    def test_admin_with_csrf_queues_run_without_collection(self):
        from osmanager.system_management.models import InspectionRun

        plan = self._plan()
        token = self._login()
        response = self.client.post(
            f'{self.base}/run', {'plan_id': plan.pk}, content_type='application/json',
            HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.json()['phase'], 'queued')
        queued = InspectionRun.objects.get()
        self.assertEqual(response.json()['id'], queued.pk)
        self.assertEqual((queued.actor, queued.plan_id), ('operator', plan.pk))
        self.assertEqual(queued.phase, 'queued')
        self.assertEqual(queued.parameters, plan.parameters)
        self.assertIsNone(queued.started_at)
        self.collect.assert_not_called()
        self.probe.assert_not_called()
        self.metric.assert_not_called()


