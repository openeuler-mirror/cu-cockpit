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