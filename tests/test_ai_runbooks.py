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
    generate_runbook,
    issue_step_confirmation,
    require_runbook_owner,
    retry_runbook_step,
    skip_runbook_step,
)
from osmanager.system_management.ai_tools import AIToolValidationError


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

    def test_invalid_confirmation_token_preserves_waiting_state(self):
        expected_hash = hashlib.sha256(b'expected-token').hexdigest()
        step = SimpleNamespace(
            status='awaiting_confirmation', confirmation_token_hash=expected_hash,
            confirmed_at=None, save=Mock(),
        )

        with self.assertRaisesRegex(AIRunbookError, '确认令牌无效'):
            consume_step_confirmation(step, 'wrong-token')

        self.assertEqual(step.status, 'awaiting_confirmation')
        self.assertEqual(step.confirmation_token_hash, expected_hash)
        self.assertIsNone(step.confirmed_at)
        step.save.assert_not_called()


class RunbookStateMachineTest(TestCase):
    def test_generated_runbook_strips_derived_step_fields_before_creation(self):
        normalized = {
            'title': 'diagnose',
            'steps': [{
                'position': 0, 'title': 'check', 'risk': 'readonly',
                'tool_call': {'tool': 'service.status', 'arguments': {'service': 'sshd'}},
            }],
        }
        with patch('osmanager.system_management.ai_runbooks.generate_runbook_payload', return_value=normalized):
            with patch('osmanager.system_management.ai_runbooks.create_runbook', return_value='runbook') as create:
                self.assertEqual(generate_runbook('diagnose', 'alice'), 'runbook')
        step = create.call_args.args[0]['steps'][0]
        self.assertEqual(set(step), {'title', 'tool_call'})

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

    def test_policy_rejection_keeps_runbook_step_pending(self):
        runbook = SimpleNamespace(actor='viewer', status='running', save=Mock())
        step = SimpleNamespace(
            status='pending', risk='change', confirmed_at='confirmed', save=Mock(),
            tool_call={'tool': 'service.restart', 'arguments': {'service': 'nginx'}},
        )

        with patch('osmanager.system_management.ai_runbooks.current_runbook_step', return_value=step):
            with self.assertRaisesRegex(AIToolValidationError, '需要管理员权限'):
                advance_runbook(runbook, 'viewer', False)

        self.assertEqual(step.status, 'pending')
        self.assertEqual(runbook.status, 'running')
        step.save.assert_not_called()
        runbook.save.assert_not_called()

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
