"""Offline inspection core regressions with isolated collectors and child processes."""

import subprocess
import sys
import unittest
from contextlib import ExitStack
from unittest.mock import patch

from osmanager.system_management import alerts, inspection, inspection_collectors, monitoring


class InspectionCenterTest(unittest.TestCase):
    """Exercise the synchronous core without Django setup or host commands."""

    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.run_readonly = inspection_collectors._run_readonly
        self.popen = subprocess.Popen
        self.children = []
        self.metrics = {
            name: self.stack.enter_context(patch.object(monitoring, name, return_value=10))
            for name in ('collect_cpu_percent', 'collect_memory_percent',
                         'collect_root_percent', 'collect_inode_percent')
        }
        self.query = self.stack.enter_context(patch.object(
            inspection_collectors, '_run_readonly', side_effect=lambda args, **kwargs:
            subprocess.CompletedProcess(args, 0, stdout=(
                'NTPSynchronized=yes\n' if args[0] == 'timedatectl' else
                'LoadState=loaded\nActiveState=active\nSubState=running\nResult=success\n'),
                stderr=''),
        ))
        self.sample = self.stack.enter_context(patch.object(
            monitoring, 'collect_metric_sample', side_effect=AssertionError('Unexpected write'),
        ))
        self.evaluate = self.stack.enter_context(patch.object(
            alerts, 'evaluate_alert_rules', side_effect=AssertionError('Unexpected alert'),
        ))

    def _start_child(self, *args, **kwargs):
        process = self.popen(*args, **kwargs)
        self.children.append(process)
        if process.stdout is not None:
            self.addCleanup(process.stdout.close)
        self.addCleanup(process.wait)
        self.addCleanup(lambda: process.kill() if process.poll() is None else None)
        return process

    def test_percent_template_boundaries_are_inclusive(self):
        self.assertEqual(inspection.INSPECTION_TEMPLATE['warning'], 80)
        self.assertEqual(inspection.INSPECTION_TEMPLATE['fail'], 90)
        for value, expected in ((0, 'pass'), (79.99, 'pass'), (80, 'warning'),
                                (89.99, 'warning'), (90, 'fail'), (100, 'fail')):
            with self.subTest(value=value):
                evidence = {'observed_percent': value}
                result = inspection_collectors.percent_result(value, evidence)
                self.assertEqual(result['status'], expected)
                self.assertEqual(result['value'], value)
                self.assertEqual(result['unit'], '%')
                self.assertEqual(result['threshold'], {
                    'warning': 80, 'fail': 90, 'operator': '>=',
                })
                self.assertIs(result['evidence'], evidence)

    def test_unregistered_service_is_rejected_before_collection(self):
        with self.assertRaisesRegex(ValueError, 'Service unit is not registered'):
            inspection.run_inspection({'services': ['unregistered.service']})
        self.query.assert_not_called()
        for collector in self.metrics.values():
            collector.assert_not_called()
        self.sample.assert_not_called()
        self.evaluate.assert_not_called()


if __name__ == '__main__':
    unittest.main()
