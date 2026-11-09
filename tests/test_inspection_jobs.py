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