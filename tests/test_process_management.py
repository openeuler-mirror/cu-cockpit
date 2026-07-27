import os
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'osmanager.settings')

import django
django.setup()

from django.test import TestCase
from rest_framework.test import APIClient

from osmanager.system_management.command import CommandResult
from osmanager.system_management.processes import list_processes, parse_ps_output, redact_command, send_process_signal


PS_OUTPUT = """  1  0 root S 0.0 0.1 100 systemd /usr/lib/systemd/systemd
 20  1 root R 4.5 1.2 30 worker /usr/bin/worker --task safe
 21  1 app S 1.0 0.5 20 helper /usr/bin/helper
"""


class ProcessServiceTest(TestCase):
    def test_command_secrets_are_redacted(self):
        value = redact_command('client --password secret --api-key=abc https://user:pass@example.test/path')
        self.assertNotIn(' secret', value)
        self.assertNotIn('=abc', value)
        self.assertNotIn(':pass@', value)
        self.assertEqual(value.count('[REDACTED]'), 3)

    @patch('osmanager.system_management.processes._platform_pids', return_value={1})
    def test_parse_processes_and_protection(self, _pids):
        items = parse_ps_output(PS_OUTPUT)
        self.assertEqual(len(items), 3)
        self.assertTrue(items[0]['protected'])
        self.assertEqual(items[1]['status'], 'running')

    @patch('osmanager.system_management.processes.run_safe', return_value=CommandResult(0, PS_OUTPUT, '', 5, False, False))
    @patch('osmanager.system_management.processes._platform_pids', return_value={1})
    def test_search_and_sort(self, _pids, _run):
        data = list_processes(search='root', sort='cpu', order='desc')
        self.assertEqual([item['pid'] for item in data['items']], [20, 1])

    @patch('osmanager.system_management.processes.os.kill')
    @patch('osmanager.system_management.processes.get_process_detail')
    def test_signal_requires_matching_pid(self, detail, kill):
        detail.return_value = {'pid': 20, 'name': 'worker', 'protected': False, 'protected_reason': ''}
        with self.assertRaises(ValueError):
            send_process_signal(20, 'TERM', 21)
        kill.assert_not_called()

    @patch('osmanager.system_management.processes.os.kill')
    @patch('osmanager.system_management.processes.get_process_detail')
    def test_protected_process_is_not_signalled(self, detail, kill):
        detail.return_value = {'pid': 1, 'name': 'systemd', 'protected': True, 'protected_reason': 'protected'}
        with self.assertRaises(ValueError):
            send_process_signal(1, 'KILL', 1)
        kill.assert_not_called()


class ProcessApiTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        session = self.client.session
        session['username'] = 'root'
        session.save()

    @patch('osmanager.system_management.views.list_processes', return_value={'items': [], 'summary': {'total': 0}})
    def test_list_is_readable(self, _list):
        response = self.client.get('/api/system/processes')
        self.assertEqual(response.status_code, 200)

    @patch('osmanager.system_management.permissions.pwd.getpwnam', return_value=SimpleNamespace(pw_uid=1000))
    def test_viewer_cannot_signal(self, _identity):
        response = self.client.post('/api/system/processes/20/signal', {'signal': 'TERM', 'confirm_pid': 20}, format='json')
        self.assertEqual(response.status_code, 403)

    @patch('osmanager.system_management.permissions.pwd.getpwnam', return_value=SimpleNamespace(pw_uid=0))
    @patch('osmanager.system_management.views.send_process_signal', side_effect=ValueError('系统初始化进程受保护'))
    def test_protected_signal_returns_400(self, _signal, _identity):
        response = self.client.post('/api/system/processes/1/signal', {'signal': 'KILL', 'confirm_pid': 1}, format='json')
        self.assertEqual(response.status_code, 400)