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

    def test_network_counters_exclude_loopback(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'dev'
            path.write_text(
                'lo: 100 0 0 0 0 0 0 0 200 0\neth0: 1000 0 0 0 0 0 0 0 2000 0\n',
                encoding='utf-8',
            )
            self.assertEqual(collect_network_bytes(path), {
                'network_rx_bytes': 1000, 'network_tx_bytes': 2000,
            })

    @patch('osmanager.system_management.monitoring.collect_service_states', return_value={'crond': 'active'})
    @patch('osmanager.system_management.monitoring.collect_network_bytes', return_value={'network_rx_bytes': 1, 'network_tx_bytes': 2})
    @patch('osmanager.system_management.monitoring.collect_inode_percent', return_value=30)
    @patch('osmanager.system_management.monitoring.collect_root_percent', return_value=20)
    @patch('osmanager.system_management.monitoring.collect_memory_percent', side_effect=MetricCollectionError('failed'))
    @patch('osmanager.system_management.monitoring.collect_cpu_percent', return_value=10)
    def test_partial_collection_preserves_valid_metrics(self, *_mocks):
        values = collect_metric_values()
        self.assertEqual(values['cpu_percent'], 10)
        self.assertIsNone(values['memory_percent'])
        self.assertEqual(values['root_percent'], 20)
        self.assertEqual(values['services'], {'crond': 'active'})


class AlertRuleStateTest(TestCase):
    def test_high_threshold_requires_lower_recovery_value(self):
        with self.assertRaisesRegex(AlertRuleValidationError, '恢复阈值必须低于'):
            normalize_alert_rule({
                'name': 'CPU high', 'metric': 'cpu_percent', 'operator': 'gte',
                'threshold': 80, 'recovery_threshold': 80,
            })

    def test_alert_requires_all_consecutive_trigger_samples(self):
        rule = SimpleNamespace(operator='gte', threshold=80, consecutive_hits=3)
        self.assertTrue(consecutive_triggered(rule, [90, 85, 80]))
        self.assertFalse(consecutive_triggered(rule, [90, 85]))
        self.assertFalse(consecutive_triggered(rule, [90, 79, 85]))

    def test_alert_requires_all_consecutive_recovery_samples(self):
        rule = SimpleNamespace(operator='gte', recovery_threshold=70, consecutive_hits=2)
        self.assertTrue(consecutive_recovered(rule, [65, 70]))
        self.assertFalse(consecutive_recovered(rule, [65]))
        self.assertFalse(consecutive_recovered(rule, [65, 71]))
