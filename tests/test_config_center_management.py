import os
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'osmanager.settings')

import django
django.setup()

from django.test import TestCase
from rest_framework.test import APIClient

from osmanager.system_management.config_center import (
    OperationConflict,
    normalize_ntp_sources,
    parse_chrony_sources,
    replace_chrony_sources,
    set_selinux_mode,
    validate_account_name,
)


class ConfigCenterServiceTest(TestCase):
    def test_parse_and_replace_chrony_sources(self):
        content = '# config\npool old.example iburst\ndriftfile /var/lib/chrony/drift\n'
        self.assertEqual(parse_chrony_sources(content)[0]['address'], 'old.example')
        updated = replace_chrony_sources(content, [
            {'mode': 'server', 'address': '10.0.0.1', 'iburst': True},
            {'mode': 'pool', 'address': 'pool.ntp.org', 'iburst': False},
        ])
        self.assertIn('server 10.0.0.1 iburst', updated)
        self.assertIn('pool pool.ntp.org', updated)
        self.assertNotIn('old.example', updated)
        self.assertIn('driftfile /var/lib/chrony/drift', updated)

    def test_invalid_ntp_source_is_rejected(self):
        with self.assertRaises(ValueError):
            normalize_ntp_sources([{'mode': 'server', 'address': 'bad host;rm'}])

    def test_invalid_account_name_is_rejected(self):
        for value in ('Root', 'bad user', '../root', 'name;id'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_account_name(value)

    @patch('osmanager.system_management.config_center.get_selinux_status', return_value={'runtime': 'Disabled'})
    def test_disabled_selinux_cannot_switch(self, _status):
        with self.assertRaises(OperationConflict):
            set_selinux_mode('enforcing')


class ConfigCenterApiTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        session = self.client.session
        session['username'] = 'root'
        session.save()

    @patch('osmanager.system_management.permissions.pwd.getpwnam', return_value=SimpleNamespace(pw_uid=0))
    @patch('osmanager.system_management.views.list_accounts', return_value={'users': [], 'groups': [], 'shells': []})
    @patch('osmanager.system_management.views.get_selinux_status', return_value={'runtime': 'Disabled', 'configured': {}})
    @patch('osmanager.system_management.views.get_ntp_status', return_value={'service_state': 'active', 'sources': []})
    def test_overview_returns_structured_status(self, _ntp, _selinux, _accounts, _identity):
        response = self.client.get('/api/system/config-center/overview')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['selinux']['runtime'], 'Disabled')

    @patch('osmanager.system_management.permissions.pwd.getpwnam', return_value=SimpleNamespace(pw_uid=0))
    def test_root_user_is_protected(self, _identity):
        response = self.client.post('/api/system/config-center/users/root/update', {'locked': True}, format='json')
        self.assertEqual(response.status_code, 400)

    @patch('osmanager.system_management.permissions.pwd.getpwnam', return_value=SimpleNamespace(pw_uid=0))
    def test_invalid_ntp_input_returns_400(self, _identity):
        response = self.client.post('/api/system/config-center/ntp/update', {
            'enabled': True,
            'sources': [{'mode': 'server', 'address': 'bad host'}],
        }, format='json')
        self.assertEqual(response.status_code, 400)

    @patch('osmanager.system_management.permissions.pwd.getpwnam', return_value=SimpleNamespace(pw_uid=1000))
    def test_viewer_cannot_create_group(self, _identity):
        response = self.client.post('/api/system/config-center/groups', {'name': 'safe_group'}, format='json')
        self.assertEqual(response.status_code, 403)