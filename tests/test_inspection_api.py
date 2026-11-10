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