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


if __name__ == '__main__':
    unittest.main()
