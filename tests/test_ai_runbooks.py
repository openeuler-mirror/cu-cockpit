import hashlib
import os
from types import SimpleNamespace
from unittest.mock import Mock, patch

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'osmanager.settings')

import django
django.setup()

from django.test import TestCase

from osmanager.system_management.ai_runbooks import (
    AIRunbookError,
    advance_runbook,
    cancel_runbook,
    consume_step_confirmation,
    issue_step_confirmation,
    require_runbook_owner,
    retry_runbook_step,
    skip_runbook_step,
)


class RunbookConfirmationTest(TestCase):
    def test_confirmation_token_is_stored_as_hash(self):
        step = SimpleNamespace(status='pending', confirmation_token_hash='', save=Mock())
        with patch('secrets.token_urlsafe', return_value='plain-token'):
            token = issue_step_confirmation(step)
        self.assertEqual(token, 'plain-token')
        self.assertEqual(step.status, 'awaiting_confirmation')
        self.assertEqual(step.confirmation_token_hash, hashlib.sha256(b'plain-token').hexdigest())
        self.assertNotIn('plain-token', step.confirmation_token_hash)


class RunbookStateMachineTest(TestCase):
    pass
