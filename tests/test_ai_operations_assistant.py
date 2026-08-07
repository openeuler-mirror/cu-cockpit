import os
from types import SimpleNamespace
from unittest.mock import Mock, patch

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'osmanager.settings')

import django
django.setup()

from django.test import TestCase

from osmanager.system_management.ai_context import prepare_context, wrap_untrusted_context
from osmanager.system_management.ai_planner import AIPlanValidationError, validate_plan_payload
from osmanager.system_management.ai_provider import AIProviderConfig, provider_status
from osmanager.system_management.ai_tools import (
    AIToolExecutionContext,
    AIToolSpec,
    AIToolValidationError,
    AI_TOOLS,
    execute_tool_call,
    normalize_service_status,
    normalize_tool_call,
)


class AIProviderTest(TestCase):
    def test_missing_provider_configuration_is_reported_without_key(self):
        config = AIProviderConfig('', 'secret-key', '', 30)
        result = provider_status(config)
        self.assertFalse(result['available'])
        self.assertEqual(result['reason'], '缺少配置: AI_BASE_URL, AI_MODEL')
        self.assertNotIn('secret-key', str(result))


class AIToolSafetyTest(TestCase):
    def test_unregistered_shell_tool_is_rejected(self):
        with self.assertRaisesRegex(AIToolValidationError, '工具未注册'):
            normalize_tool_call({
                'tool': 'shell.execute',
                'arguments': {'command': 'rm -rf /'},
            })

    def test_unknown_arguments_are_rejected_for_registered_tool(self):
        with self.assertRaisesRegex(AIToolValidationError, 'command, shell'):
            normalize_tool_call({
                'tool': 'service.status',
                'arguments': {'service': 'sshd', 'command': 'id', 'shell': True},
            })


class AIContextSafetyTest(TestCase):
    pass


class AIPlanSafetyTest(TestCase):
    pass
