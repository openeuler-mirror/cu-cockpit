import os
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'osmanager.settings')

import django
django.setup()

from django.test import TestCase
from rest_framework.test import APIClient

from osmanager.system_management.command import CommandExecutionTimeout, UnsafeCommandError, run_safe
from osmanager.system_management.models import ConfigSnapshot, OperationAudit
from osmanager.system_management.security import REDACTED, sanitize_detail
from osmanager.system_management.snapshots import (
    create_snapshot,
    diff_snapshot,
    register_snapshot_target,
    rollback_snapshot,
)


class FoundationApiTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def login_as(self, username):
        session = self.client.session
        session['username'] = username
        session.save()

    def test_context_requires_login(self):
        response = self.client.get('/api/system/context')
        self.assertEqual(response.status_code, 401)

    @patch('osmanager.system_management.permissions.pwd.getpwnam', return_value=SimpleNamespace(pw_uid=0))
    def test_context_uses_posix_uid_for_admin(self, _getpwnam):
        self.login_as('sysadmin')
        response = self.client.get('/api/system/context')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['identity']['role'], 'admin')
        self.assertTrue(response.json()['identity']['is_admin'])

    @patch('osmanager.system_management.permissions.pwd.getpwnam', return_value=SimpleNamespace(pw_uid=1000))
    def test_admin_endpoint_rejects_viewer_and_audits(self, _getpwnam):
        self.login_as('viewer')
        response = self.client.get('/api/system/audits')
        self.assertEqual(response.status_code, 403)
        audit = OperationAudit.objects.get()
        self.assertEqual(audit.action, 'permission_denied')
        self.assertFalse(audit.success)

    @patch('osmanager.system_management.views.detect_capabilities', return_value={'modules': {'cron': {'available': True}}})
    def test_capabilities_is_available_to_logged_in_user(self, _detect):
        self.login_as('viewer')
        response = self.client.get('/api/system/capabilities')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['modules']['cron']['available'])

    @patch('osmanager.system_management.permissions.pwd.getpwnam', return_value=SimpleNamespace(pw_uid=1000))
    def test_viewer_cannot_use_existing_privileged_endpoints(self, _getpwnam):
        self.login_as('viewer')
        requests = (
            ('/api/config/set/config.sh', {'hostname': 'safe-host'}),
            ('/api/service/manage', {'service_name': 'sshd', 'operation': 'restart'}),
            ('/api/terminal/connect', {'hostname': '127.0.0.1', 'port': '22', 'username': 'root', 'password': 'secret'}),
        )
        for path, data in requests:
            with self.subTest(path=path):
                response = self.client.post(path, data, format='json')
                self.assertEqual(response.status_code, 403)

    @patch('osmanager.system_management.permissions.pwd.getpwnam', return_value=SimpleNamespace(pw_uid=0))
    def test_admin_service_name_validation_runs_before_script(self, _getpwnam):
        self.login_as('root')
        response = self.client.post('/api/service/manage', {
            'service_name': 'sshd invalid',
            'operation': 'restart',
        }, format='json')
        self.assertEqual(response.status_code, 400)


class SafeCommandTest(TestCase):
    def test_rejects_non_whitelisted_command(self):
        with self.assertRaises(UnsafeCommandError):
            run_safe(['echo', 'ok'], {'uname'})

    def test_rejects_newline_argument(self):
        with self.assertRaises(UnsafeCommandError):
            run_safe(['printf', 'unsafe\nvalue'], {'printf'})

    def test_runs_explicit_argv_without_shell(self):
        result = run_safe(['printf', '%s', 'safe value'], {'printf'})
        self.assertEqual(result.stdout, 'safe value')
        self.assertTrue(result.success)

    def test_timeout_is_structured(self):
        with self.assertRaises(CommandExecutionTimeout) as context:
            run_safe(['sleep', '1'], {'sleep'}, timeout=0.1)
        self.assertTrue(context.exception.to_dict()['timed_out'])


class AuditAndSnapshotTest(TestCase):
    def test_sensitive_detail_is_redacted(self):
        sanitized = sanitize_detail({'password': 'secret', 'nested': {'private_key': 'key'}, 'name': 'safe'})
        self.assertEqual(sanitized['password'], REDACTED)
        self.assertEqual(sanitized['nested']['private_key'], REDACTED)
        self.assertEqual(sanitized['name'], 'safe')

    def test_snapshot_diff_and_rollback(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'managed.conf'
            path.write_text('value=one\n', encoding='utf-8')
            target = f'test-{id(self)}'
            register_snapshot_target(target, path)
            snapshot = create_snapshot('root', 'test', target, 'before change')
            path.write_text('value=two\n', encoding='utf-8')
            self.assertIn('-value=one', diff_snapshot(snapshot))
            self.assertIn('+value=two', diff_snapshot(snapshot))
            safety_snapshot = rollback_snapshot(snapshot, 'root')
            self.assertEqual(path.read_text(encoding='utf-8'), 'value=one\n')
            self.assertEqual(ConfigSnapshot.objects.count(), 2)
            self.assertEqual(safety_snapshot.content, 'value=two\n')

    def test_unregistered_snapshot_target_is_rejected(self):
        with self.assertRaises(ValueError):
            create_snapshot('root', 'test', 'not-registered')