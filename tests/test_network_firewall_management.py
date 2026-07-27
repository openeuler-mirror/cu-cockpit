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

from osmanager.system_management.config_center import OperationConflict
from osmanager.system_management.network import merge_interfaces, parse_listeners, read_dns, update_firewall_rule


class NetworkServiceTest(TestCase):
    def test_merge_interfaces_marks_virtual_types(self):
        links = [
            {'ifindex': 1, 'ifname': 'lo', 'flags': ['UP'], 'mtu': 65536, 'operstate': 'UNKNOWN'},
            {'ifindex': 2, 'ifname': 'ens33', 'flags': ['UP', 'LOWER_UP'], 'link_type': 'ether', 'mtu': 1500, 'operstate': 'UP'},
            {'ifindex': 3, 'ifname': 'veth123', 'flags': ['UP'], 'link_type': 'ether', 'mtu': 1500, 'operstate': 'UP'},
        ]
        addresses = [{'ifindex': 2, 'addr_info': [{'family': 'inet', 'local': '10.0.0.2', 'prefixlen': 24}]}]
        items = merge_interfaces(links, addresses)
        self.assertEqual([item['type'] for item in items], ['loopback', 'ethernet', 'veth'])
        self.assertEqual(items[1]['addresses'][0]['local'], '10.0.0.2')

    def test_parse_dns_and_listeners(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'resolv.conf'
            path.write_text('nameserver 1.1.1.1\nsearch example.test\noptions timeout:1\n', encoding='utf-8')
            dns = read_dns(path)
            self.assertEqual(dns['nameservers'], ['1.1.1.1'])
            self.assertEqual(dns['search'], ['example.test'])
        output = 'tcp LISTEN 0 128 127.0.0.1:8000 0.0.0.0:* users:(("gunicorn",pid=10,fd=3))\n'
        listener = parse_listeners(output)[0]
        self.assertEqual(listener['local_port'], '8000')
        self.assertEqual(listener['processes'][0]['name'], 'gunicorn')

    @patch('osmanager.system_management.network.firewall_status', return_value={'active': False, 'reason': 'inactive'})
    def test_inactive_firewall_rejects_write(self, _status):
        with self.assertRaises(OperationConflict):
            update_firewall_rule({'action': 'add', 'zone': 'public', 'rule_type': 'port', 'value': '80', 'protocol': 'tcp'})


class NetworkApiTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        session = self.client.session
        session['username'] = 'root'
        session.save()

    @patch('osmanager.system_management.views.network_overview', return_value={'summary': {'interfaces': 1}, 'interfaces': []})
    def test_overview_is_readable(self, _overview):
        response = self.client.get('/api/system/network/overview')
        self.assertEqual(response.status_code, 200)

    @patch('osmanager.system_management.permissions.pwd.getpwnam', return_value=SimpleNamespace(pw_uid=0))
    @patch('osmanager.system_management.views.update_firewall_rule', side_effect=OperationConflict('firewalld 服务未运行'))
    def test_inactive_firewall_returns_409(self, _update, _identity):
        response = self.client.post('/api/system/network/firewall/rules/update', {
            'action': 'add', 'zone': 'public', 'rule_type': 'port', 'value': '80', 'protocol': 'tcp',
        }, format='json')
        self.assertEqual(response.status_code, 409)

    @patch('osmanager.system_management.permissions.pwd.getpwnam', return_value=SimpleNamespace(pw_uid=1000))
    def test_viewer_cannot_write_firewall(self, _identity):
        response = self.client.post('/api/system/network/firewall/rules/update', {}, format='json')
        self.assertEqual(response.status_code, 403)