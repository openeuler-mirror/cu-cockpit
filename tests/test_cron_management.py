import os
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'osmanager.settings')

import django
django.setup()

from django.test import TestCase
from rest_framework.test import APIClient

from osmanager.system_management.command import CommandResult
from osmanager.system_management.cron import parse_job_command, validate_schedule
from osmanager.system_management.models import CronExecution, CronJob


class CronValidationTest(TestCase):
    def test_valid_schedule_is_normalized(self):
        self.assertEqual(validate_schedule('*/5  * * * 1-5'), '*/5 * * * 1-5')

    def test_invalid_schedule_is_rejected(self):
        for value in ('* * * *', '@daily', '* * * * *;id'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_schedule(value)

    def test_safe_command_is_parsed(self):
        self.assertEqual(parse_job_command('logger "cron ok"'), ['logger', 'cron ok'])

    def test_shell_command_is_rejected(self):
        for value in ('sh -c id', 'echo ok | logger', 'echo $(id)', 'echo ok > /tmp/x'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                parse_job_command(value)


class CronApiTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        session = self.client.session
        session['username'] = 'root'
        session.save()

    @patch('osmanager.system_management.permissions.pwd.getpwnam', return_value=SimpleNamespace(pw_uid=0))
    @patch('osmanager.system_management.cron.sync_cron_file')
    def test_crud_and_history(self, _sync, _identity):
        response = self.client.post('/api/system/cron/jobs/create', {
            'name': 'test job', 'schedule': '*/10 * * * *', 'command': 'true', 'enabled': True,
        }, format='json')
        self.assertEqual(response.status_code, 200)
        job_id = response.json()['item']['id']
        response = self.client.post(f'/api/system/cron/jobs/{job_id}/update', {
            'schedule': '*/15 * * * *', 'enabled': False,
        }, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()['item']['enabled'])
        response = self.client.get('/api/system/cron/jobs')
        self.assertEqual(len(response.json()['items']), 1)
        response = self.client.post(f'/api/system/cron/jobs/{job_id}/delete', {}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(CronJob.objects.exists())

    @patch('osmanager.system_management.permissions.pwd.getpwnam', return_value=SimpleNamespace(pw_uid=0))
    @patch('osmanager.system_management.cron.run_safe', return_value=CommandResult(0, 'ok\n', '', 4, False, False))
    def test_manual_execution_creates_history(self, _run, _identity):
        job = CronJob.objects.create(name='run', schedule='* * * * *', command=['true'], enabled=False,
                                    created_by='root', updated_by='root')
        response = self.client.post(f'/api/system/cron/jobs/{job.id}/run', {}, format='json')
        self.assertEqual(response.status_code, 200)
        execution = CronExecution.objects.get()
        self.assertTrue(execution.manual)
        self.assertEqual(execution.status, 'success')

    @patch('osmanager.system_management.permissions.pwd.getpwnam', return_value=SimpleNamespace(pw_uid=1000))
    def test_viewer_cannot_create_job(self, _identity):
        response = self.client.post('/api/system/cron/jobs/create', {
            'name': 'blocked', 'schedule': '* * * * *', 'command': 'true',
        }, format='json')
        self.assertEqual(response.status_code, 403)