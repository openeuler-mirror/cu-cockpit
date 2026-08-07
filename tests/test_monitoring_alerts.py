import os
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'osmanager.settings')

import django
django.setup()

from django.test import TestCase

from osmanager.system_management.alerts import (
    AlertRuleValidationError,
    consecutive_recovered,
    consecutive_triggered,
    normalize_alert_rule,
)
from osmanager.system_management.monitoring import (
    MetricCollectionError,
    collect_memory_percent,
    collect_metric_values,
    collect_network_bytes,
)


class MetricCollectorTest(TestCase):
    pass


class AlertRuleStateTest(TestCase):
    pass
