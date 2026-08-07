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
    pass


class AIToolSafetyTest(TestCase):
    pass


class AIContextSafetyTest(TestCase):
    pass


class AIPlanSafetyTest(TestCase):
    pass
