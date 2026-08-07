import os
import tempfile
from datetime import timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'osmanager.settings')

import django
django.setup()

from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from osmanager.system_management.alerts import (
    AlertRuleValidationError,
    build_alert_context,
    consecutive_recovered,
    consecutive_triggered,
    evaluate_alert_rule,
    normalize_alert_rule,
)
from osmanager.system_management.monitoring import (
    MetricCollectionError,
    collect_memory_percent,
    collect_metric_values,
    collect_network_bytes,
)
from osmanager.system_management.models import AlertEvent, AlertRule, MetricSample


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
    def test_consecutive_samples_open_active_alert(self):
        rule = AlertRule.objects.create(
            name='CPU high', metric='cpu_percent', threshold=80,
            recovery_threshold=70, consecutive_hits=3,
        )
        MetricSample.objects.create(cpu_percent=82)
        MetricSample.objects.create(cpu_percent=85)
        sample = MetricSample.objects.create(cpu_percent=91)

        event = evaluate_alert_rule(rule, sample)

        self.assertEqual(event.status, 'active')
        self.assertEqual(event.trigger_value, 91)
        self.assertEqual(event.context, {'sample_id': sample.id, 'values': [91, 85, 82]})

    def test_consecutive_recovery_samples_close_active_alert(self):
        rule = AlertRule.objects.create(
            name='CPU high', metric='cpu_percent', threshold=80,
            recovery_threshold=70, consecutive_hits=2,
        )
        AlertEvent.objects.create(rule=rule, trigger_value=91, last_value=91)
        MetricSample.objects.create(cpu_percent=68)
        sample = MetricSample.objects.create(cpu_percent=65)

        event = evaluate_alert_rule(rule, sample)

        self.assertEqual(event.status, 'recovered')
        self.assertEqual(event.recovery_value, 65)
        self.assertIsNotNone(event.recovered_at)
        self.assertFalse(AlertEvent.objects.filter(rule=rule, status='active').exists())

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

    def test_rule_allows_only_one_active_event(self):
        rule = AlertRule.objects.create(
            name='CPU high', metric='cpu_percent', threshold=80,
            recovery_threshold=70, consecutive_hits=2,
        )
        AlertEvent.objects.create(rule=rule, trigger_value=90, last_value=90)
        with self.assertRaises(IntegrityError), transaction.atomic():
            AlertEvent.objects.create(rule=rule, trigger_value=95, last_value=95)

    @patch('osmanager.system_management.ai_tools.execute_log_query', return_value={'logs': []})
    def test_alert_context_bounds_logs_to_event_window(self, execute_log_query):
        rule = AlertRule.objects.create(
            name='CPU high', metric='cpu_percent', threshold=80,
            recovery_threshold=70, consecutive_hits=2,
        )
        recovered_at = timezone.now()
        started_at = recovered_at - timedelta(hours=1)
        event = AlertEvent.objects.create(
            rule=rule, status='recovered', recovered_at=recovered_at,
            trigger_value=90, last_value=60,
        )
        AlertEvent.objects.filter(id=event.id).update(started_at=started_at)
        event.refresh_from_db()

        build_alert_context(event)

        arguments = execute_log_query.call_args.args[0]
        self.assertEqual(arguments['since'], started_at - timedelta(minutes=30))
        self.assertEqual(arguments['until'], recovered_at)
