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

    def test_confirmation_token_cannot_be_reused(self):
        step = SimpleNamespace(
            status='awaiting_confirmation',
            confirmation_token_hash=hashlib.sha256(b'one-time').hexdigest(),
            confirmed_at=None,
            save=Mock(),
        )
        consume_step_confirmation(step, 'one-time')
        self.assertEqual(step.status, 'pending')
        self.assertEqual(step.confirmation_token_hash, '')
        with self.assertRaisesRegex(AIRunbookError, '不等待确认'):
            consume_step_confirmation(step, 'one-time')


class RunbookStateMachineTest(TestCase):
    def test_non_owner_cannot_operate_runbook(self):
        runbook = SimpleNamespace(actor='alice')
        with self.assertRaisesRegex(AIRunbookError, '无权操作其他用户'):
            require_runbook_owner(runbook, 'bob')

    def test_change_step_pauses_before_execution(self):
        runbook = SimpleNamespace(actor='root')
        step = SimpleNamespace(risk='change', status='pending', confirmed_at=None)
        with patch('osmanager.system_management.ai_runbooks.current_runbook_step', return_value=step):
            with patch('osmanager.system_management.ai_runbooks.pause_runbook_for_confirmation', return_value='token'):
                with patch('osmanager.system_management.ai_runbooks.execute_runbook_step') as executor:
                    outcome = advance_runbook(runbook, 'root', True)
        self.assertEqual(outcome['action'], 'confirmation_required')
        self.assertEqual(outcome['confirmation_token'], 'token')
        executor.assert_not_called()

    def test_retry_requires_change_step_reconfirmation(self):
        runbook = SimpleNamespace(actor='root', status='failed', error='failed', save=Mock())
        step = SimpleNamespace(
            status='failed', risk='change', output={'old': True}, error='failed',
            confirmed_at='old-confirmation', started_at='start', finished_at='finish', save=Mock(),
        )
        with patch('osmanager.system_management.ai_runbooks.current_runbook_step', return_value=step):
            retry_runbook_step(runbook, 'root')
        self.assertEqual(step.status, 'pending')
        self.assertIsNone(step.confirmed_at)
        self.assertEqual(runbook.status, 'running')

    def test_failed_change_step_cannot_be_skipped(self):
        runbook = SimpleNamespace(actor='root')
        step = SimpleNamespace(status='failed', risk='change')
        with patch('osmanager.system_management.ai_runbooks.current_runbook_step', return_value=step):
            with self.assertRaisesRegex(AIRunbookError, '只能跳过失败的只读步骤'):
                skip_runbook_step(runbook, 'root')

    def test_cancel_preserves_succeeded_steps(self):
        pending = SimpleNamespace(update=Mock(return_value=2))
        steps = SimpleNamespace(filter=Mock(return_value=pending))
        runbook = SimpleNamespace(
            actor='alice', status='running', current_step=1, error='', steps=steps, save=Mock(),
        )
        cancel_runbook(runbook, 'alice')
        statuses = steps.filter.call_args.kwargs['status__in']
        self.assertNotIn('succeeded', statuses)
        self.assertEqual(steps.filter.call_args.kwargs['position__gte'], 1)
        self.assertEqual(runbook.status, 'cancelled')
