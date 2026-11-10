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

    def test_unsafe_or_unknown_run_payload_is_rejected_without_enqueue(self):
        from osmanager.system_management.models import InspectionRun

        token = self._login()
        payloads = (
            {'parameters': {}, 'script': 'touch /tmp/inspection-injected'},
            {'parameters': {}, 'path': '../../etc/shadow'},
            {'parameters': {}, 'unknown': True},
        )
        with patch('osmanager.system_management.inspection_jobs.queue_run') as enqueue:
            for payload in payloads:
                with self.subTest(payload=payload):
                    response = self.client.post(
                        f'{self.base}/run', payload, content_type='application/json',
                        HTTP_X_CSRFTOKEN=token)
                    self.assertEqual(response.status_code, 400)
                    self.assertEqual(response.json()['code'], 400)
                    enqueue.assert_not_called()
                    self.assertEqual(InspectionRun.objects.count(), 0)
        self.collect.assert_not_called()
        self.probe.assert_not_called()
        self.metric.assert_not_called()

    def _run(self, actor='operator'):
        from django.utils import timezone
        from osmanager.system_management.inspection_jobs import queue_run
        from osmanager.system_management.models import InspectionRun

        plan = self._plan(actor=actor)
        queued = queue_run(actor, plan_id=plan.pk)
        observed_at = timezone.now()
        InspectionRun.objects.filter(pk=queued.pk).update(
            phase='finished', health='fail', duration=0.25,
            started_at=observed_at, finished_at=observed_at,
            items=[{
                'id': 'service:nginx.service', 'status': 'fail',
                'value': {'ActiveState': 'inactive'}, 'unit': None,
                'threshold': {'ActiveState': 'active'},
                'reason': 'nginx.service: ActiveState=inactive',
                'evidence': {'output': '<script>alert("inspection")</script>&',
                             'returncode': 0,
                             'command': ['systemctl', 'show', '--', 'nginx.service']},
            }])
        queued.refresh_from_db()
        return queued

    def test_other_actor_cannot_queue_or_read_owned_inspection(self):
        from osmanager.system_management.models import InspectionRun

        stored = self._run()
        token = self._login('other-admin')
        before = list(InspectionRun.objects.values())
        requests = (
            ('post', '/run', {'plan_id': stored.plan_id}),
            ('get', f'/runs/{stored.pk}', {}),
            ('get', f'/runs/{stored.pk}/report', {'format': 'json'}),
            ('get', f'/runs/{stored.pk}/report', {'format': 'html'}),
        )
        for method, suffix, payload in requests:
            with self.subTest(method=method, suffix=suffix, payload=payload):
                response = getattr(self.client, method)(
                    f'{self.base}{suffix}', payload, content_type='application/json',
                    HTTP_X_CSRFTOKEN=token)
                self.assertEqual(response.status_code, 404)
                self.assertEqual(response.json()['code'], 404)
                self.assertEqual(list(InspectionRun.objects.values()), before)
        self.account.assert_called_with('other-admin')
        self.collect.assert_not_called()
        self.probe.assert_not_called()
        self.metric.assert_not_called()

    def test_html_report_escapes_stored_evidence_without_recollection(self):
        import json
        from django.utils.html import escape

        stored = self._run()
        unsafe = stored.items[0]['evidence']['output']
        self._login()
        response = self.client.get(
            f'{self.base}/runs/{stored.pk}/report', {'format': 'html'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/html; charset=utf-8')
        self.assertEqual(response['Content-Disposition'],
                         f'attachment; filename="inspection-{stored.pk}.html"')
        self.assertEqual(response['Cache-Control'], 'private, no-store')
        body = response.content.decode('utf-8')
        self.assertIn(str(escape(json.dumps(unsafe))), body)
        self.assertNotIn(unsafe, body)
        self.assertNotIn('<script>', body)
        stored.refresh_from_db()
        self.assertEqual(stored.items[0]['evidence']['output'], unsafe)
        self.collect.assert_not_called()
        self.probe.assert_not_called()
        self.metric.assert_not_called()

    def test_json_report_preserves_complete_persisted_snapshot(self):
        import json
        from django.core.serializers.json import DjangoJSONEncoder

        stored = self._run()
        self._login()
        fields = (
            'id', 'plan_id', 'plan_snapshot', 'trigger', 'actor', 'template_id', 'version',
            'parameters', 'phase', 'health', 'scheduled_slot', 'queued_at', 'started_at',
            'finished_at', 'duration', 'items', 'error',
        )
        expected = {field: getattr(stored, field) for field in fields}
        expected['counts'] = {'pass': 0, 'warning': 0, 'fail': 1, 'error': 0, 'skipped': 0}
        response = self.client.get(
            f'{self.base}/runs/{stored.pk}/report', {'format': 'json'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json; charset=utf-8')
        self.assertEqual(response.json(), json.loads(json.dumps(expected, cls=DjangoJSONEncoder)))
        self.assertEqual((response.json()['template_id'], response.json()['version']),
                         ('local-host', 'v1'))
        self.assertEqual(response.json()['parameters'], {'services': ['nginx.service']})
        self.assertEqual((response.json()['phase'], response.json()['health']),
                         ('finished', 'fail'))
        self.collect.assert_not_called()
        self.probe.assert_not_called()
        self.metric.assert_not_called()


