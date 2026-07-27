import os
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'osmanager.settings')

import django
django.setup()

from django.test import TestCase
from rest_framework.test import APIClient


class TerminalSessionEnhancementTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        session = self.client.session
        session['username'] = 'root'
        session.save()

    def _webssh_session(self):
        session = MagicMock()
        session.cookies.get.return_value = 'xsrf'
        response = MagicMock()
        response.status_code = 200
        response.json.return_value = {'id': 'worker-1', 'encoding': 'utf-8'}
        session.post.return_value = response
        return session

    @patch('osmanager.system_management.permissions.pwd.getpwnam', return_value=SimpleNamespace(pw_uid=0))
    @patch('osmanager.web_terminal.views.requests.Session')
    def test_password_auth_forwards_whitelisted_fields(self, session_class, _identity):
        session = self._webssh_session()
        session_class.return_value = session
        response = self.client.post('/api/terminal/connect', {
            'hostname': '127.0.0.1', 'port': '22', 'username': 'root',
            'password': 'secret', 'term': 'xterm-256color', 'ignored': 'value',
        })
        self.assertEqual(response.status_code, 200)
        forwarded = session.post.call_args.kwargs['data']
        self.assertEqual(forwarded['password'], 'secret')
        self.assertEqual(forwarded['privatekey'], '')
        self.assertNotIn('ignored', forwarded)

    @patch('osmanager.system_management.permissions.pwd.getpwnam', return_value=SimpleNamespace(pw_uid=0))
    @patch('osmanager.web_terminal.views.requests.Session')
    def test_private_key_auth_is_supported(self, session_class, _identity):
        session = self._webssh_session()
        session_class.return_value = session
        private_key = '-----BEGIN OPENSSH PRIVATE KEY-----\ntest\n-----END OPENSSH PRIVATE KEY-----'
        response = self.client.post('/api/terminal/connect', {
            'hostname': 'localhost', 'port': '22', 'username': 'root',
            'privatekey': private_key, 'passphrase': 'phrase', 'term': 'xterm-256color',
        })
        self.assertEqual(response.status_code, 200)
        forwarded = session.post.call_args.kwargs['data']
        self.assertEqual(forwarded['privatekey'], private_key)
        self.assertEqual(forwarded['passphrase'], 'phrase')
        self.assertEqual(forwarded['password'], '')

    @patch('osmanager.system_management.permissions.pwd.getpwnam', return_value=SimpleNamespace(pw_uid=0))
    def test_exactly_one_auth_method_is_required(self, _identity):
        base = {'hostname': 'localhost', 'port': '22', 'username': 'root', 'term': 'xterm-256color'}
        for payload in (base, {**base, 'password': 'secret', 'privatekey': '-----BEGIN PRIVATE KEY-----\nx'}):
            with self.subTest(payload=payload):
                response = self.client.post('/api/terminal/connect', payload)
                self.assertEqual(response.status_code, 400)

    @patch('osmanager.system_management.permissions.pwd.getpwnam', return_value=SimpleNamespace(pw_uid=0))
    def test_invalid_host_and_key_are_rejected(self, _identity):
        response = self.client.post('/api/terminal/connect', {
            'hostname': 'bad host;id', 'port': '22', 'username': 'root', 'password': 'x', 'term': 'xterm',
        })
        self.assertEqual(response.status_code, 400)
        response = self.client.post('/api/terminal/connect', {
            'hostname': 'localhost', 'port': '22', 'username': 'root', 'privatekey': 'not-a-key', 'term': 'xterm',
        })
        self.assertEqual(response.status_code, 400)

    def test_default_proxy_uses_dedicated_port(self):
        from osmanager.web_terminal.views import WEBSSH_URL
        self.assertEqual(WEBSSH_URL, 'http://127.0.0.1:8002')