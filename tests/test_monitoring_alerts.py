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
    def test_memory_percentage_uses_mem_available(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'meminfo'
            path.write_text('MemTotal: 1000 kB\nMemAvailable: 250 kB\n', encoding='utf-8')
            self.assertEqual(collect_memory_percent(path), 75.0)


class AlertRuleStateTest(TestCase):
    pass
