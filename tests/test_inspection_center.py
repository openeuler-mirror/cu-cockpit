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
        self.raw_collectors = {
            name: getattr(monitoring, name)
            for name in ('collect_cpu_percent', 'collect_memory_percent')
        }
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

    def test_excess_services_are_rejected_before_collection(self):
        registered = inspection.INSPECTION_TEMPLATE['registered_services']
        services = list(registered) + [registered[0]]
        self.assertEqual(len(services), inspection.INSPECTION_TEMPLATE['max_services'] + 1)
        with self.assertRaisesRegex(ValueError, 'At most 16 services may be inspected'):
            inspection.run_inspection({'services': services})
        self.query.assert_not_called()
        for collector in self.metrics.values():
            collector.assert_not_called()

    def test_inactive_service_returns_fail_with_evidence(self):
        command = ['systemctl', 'show', '--no-pager',
                   '--property=LoadState,ActiveState,SubState,Result', '--', 'nginx.service']
        output = 'LoadState=loaded\nActiveState=inactive\nSubState=dead\nResult=success\n'
        self.query.side_effect = None
        self.query.return_value = subprocess.CompletedProcess(command, 0, stdout=output)
        result, = inspection_collectors.collect_services({'services': ['nginx.service']})
        self.assertEqual(result['id'], 'service:nginx.service')
        self.assertEqual(result['status'], 'fail')
        self.assertEqual(result['value']['ActiveState'], 'inactive')
        self.assertEqual(result['evidence']['output'], output)
        self.assertEqual(result['evidence']['returncode'], 0)
        self.assertEqual(result['evidence']['command'], command)
        self.assertEqual(result['threshold']['ActiveState'], 'active')
        self.query.assert_called_once_with(command)

    def test_not_found_service_returns_fail_despite_exit_one(self):
        command = ['systemctl', 'show', '--no-pager',
                   '--property=LoadState,ActiveState,SubState,Result', '--', 'nginx.service']
        output = 'LoadState=not-found\nActiveState=inactive\nSubState=dead\nResult=success\n'
        self.query.side_effect = None
        self.query.return_value = subprocess.CompletedProcess(command, 1, stdout=output)
        result, = inspection_collectors.collect_services({'services': ['nginx.service']})
        self.assertEqual(result['id'], 'service:nginx.service')
        self.assertEqual(result['status'], 'fail')
        self.assertEqual(result['value']['LoadState'], 'not-found')
        self.assertEqual(result['evidence']['returncode'], 1)
        self.assertEqual(result['evidence']['output'], output)
        self.assertEqual(result['evidence']['command'], command)
        self.assertNotIn('error', result['evidence'])
        self.query.assert_called_once_with(command)

    def test_time_sync_without_synchronization_evidence_returns_error(self):
        command = ['timedatectl', 'show', '--no-pager',
                   '--property=NTPSynchronized,NTP,CanNTP']
        self.query.side_effect = None
        self.query.return_value = subprocess.CompletedProcess(
            command, 0, stdout='NTP=yes\nCanNTP=yes\n',
        )
        result = inspection_collectors.collect_time_sync()
        self.assertEqual(result['id'], 'time_sync')
        self.assertEqual(result['status'], 'error')
        self.assertIsNone(result['value'])
        self.assertIsNone(result['threshold'])
        self.assertEqual(result['evidence']['error'], 'ValueError')
        self.assertIn('Invalid or missing systemd properties', result['reason'])
        self.query.assert_called_once_with(command)

    def test_metric_exception_preserves_other_items_without_writes(self):
        self.metrics['collect_cpu_percent'].side_effect = monitoring.MetricCollectionError(
            'CPU evidence unavailable',
        )
        result = inspection.run_inspection()
        self.assertEqual(set(result), {
            'template_id', 'version', 'parameters', 'items', 'status', 'duration',
        })
        self.assertEqual(result['template_id'], 'local-host')
        self.assertEqual(result['version'], 'v1')
        self.assertEqual(result['parameters'], {'services': ['cu-cockpit.service']})
        self.assertEqual(result['status'], 'error')
        self.assertEqual([item['id'] for item in result['items']], [
            'cpu', 'memory', 'root_capacity', 'root_inodes', 'time_sync',
            'service:cu-cockpit.service',
        ])
        failed, *remaining = result['items']
        self.assertEqual(failed['status'], 'error')
        self.assertEqual(failed['evidence']['error'], 'MetricCollectionError')
        self.assertIsNone(failed['value'])
        self.assertEqual(failed['reason'], 'CPU evidence unavailable')
        self.assertEqual([item['status'] for item in remaining], ['pass'] * 5)
        for item in result['items']:
            self.assertEqual(set(item), {
                'id', 'label', 'status', 'value', 'unit', 'threshold', 'evidence',
                'reason', 'duration', 'version',
            })
            self.assertEqual(item['version'], result['version'])
            self.assertGreaterEqual(item['duration'], 0)
        for collector in self.metrics.values():
            collector.assert_called_once()
        self.assertEqual(self.query.call_count, 2)
        self.sample.assert_not_called()
        self.evaluate.assert_not_called()

    def test_invalid_cpu_evidence_returns_inspection_error(self):
        query = self.query.side_effect
        with patch.object(monitoring, 'collect_cpu_percent',
                          self.raw_collectors['collect_cpu_percent']):
            for idle in ('150', '-1', '-0.1', '100.01', 'nan', 'NaN', 'inf',
                         '-Infinity', '1e309', 'invalid'):
                with self.subTest(idle=idle):
                    self.query.side_effect = lambda args, **kwargs: (
                        subprocess.CompletedProcess(args, 0, stdout=(
                            f'%Cpu(s): 99.0 id\n%Cpu(s): {idle} id\n'))
                        if args[0] == 'top' else query(args, **kwargs))
                    result = inspection.run_inspection()
                    cpu, *remaining = result['items']
                    self.assertEqual(result['status'], 'error')
                    self.assertEqual(cpu['status'], 'error')
                    self.assertEqual(cpu['evidence']['error'], 'MetricCollectionError')
                    self.assertIsNone(cpu['value'])
                    self.assertEqual([item['status'] for item in remaining], ['pass'] * 5)
        self.sample.assert_not_called()
        self.evaluate.assert_not_called()

    def test_run_deadline_skips_all_remaining_items(self):
        with patch('time.monotonic', side_effect=[0, 0, 1, 1] + [61] * 6):
            result = inspection.run_inspection()
        self.assertEqual(result['status'], 'error')
        self.assertEqual(result['duration'], 61)
        self.assertEqual([item['status'] for item in result['items']],
                         ['pass'] + ['skipped'] * 5)
        self.assertEqual([item['id'] for item in result['items'][1:]], [
            'memory', 'root_capacity', 'root_inodes', 'time_sync',
            'service:cu-cockpit.service',
        ])
        for item in result['items'][1:]:
            self.assertEqual(item['evidence'], {'deadline_exhausted': True})
            self.assertIsNone(item['value'])
            self.assertEqual(item['duration'], 0)
        self.metrics['collect_cpu_percent'].assert_called_once()
        for name in ('collect_memory_percent', 'collect_root_percent', 'collect_inode_percent'):
            self.metrics[name].assert_not_called()
        self.query.assert_not_called()
        self.assertIsNone(inspection_collectors._ITEM_DEADLINE.get())

    def test_runner_rejects_non_allowlisted_argv_before_spawn(self):
        commands = (
            ('uname', '-a'),
            ('top', '-bn1'),
            ('df', '-P', '--', '/tmp'),
            ('df', '-P', '--', '/', '--help'),
            ('systemctl', 'is-active', 'nginx.service'),
            ('systemctl', 'show', '--no-pager',
             '--property=LoadState,ActiveState,SubState,Result', '--', 'unregistered.service'),
            (sys.executable, '-c', 'print(123)'),
        )
        with patch('subprocess.Popen', side_effect=AssertionError('Unexpected spawn')) as spawn:
            for command in commands:
                with self.subTest(command=command):
                    with self.assertRaisesRegex(ValueError, 'not a built-in inspection query'):
                        self.run_readonly(command)
            spawn.assert_not_called()

    def test_output_over_limit_terminates_real_child(self):
        command = (sys.executable, '-c',
                   'import sys\nsys.stdout.write("x" * 16385)\nsys.stdout.flush()\n'
                   'while True: pass')
        with patch.object(inspection_collectors, '_validate_command',
                          return_value=command) as validate:
            with patch('subprocess.Popen', side_effect=self._start_child) as spawn:
                with self.assertRaisesRegex(RuntimeError, 'output exceeds 16 KiB'):
                    self.run_readonly(command)
        validate.assert_called_once_with(command)
        self.assertEqual(len(self.children), 1)
        process = self.children[0]
        self.assertIsNotNone(process.poll())
        self.assertLess(process.returncode, 0)
        self.assertTrue(process.stdout.closed)
        self.assertEqual(spawn.call_args.args[0], command)
        self.assertIs(spawn.call_args.kwargs['shell'], False)

    def test_timeout_terminates_real_child(self):
        command = (sys.executable, '-c', 'while True: pass')
        with patch.object(inspection_collectors, '_validate_command',
                          return_value=command) as validate:
            with patch('subprocess.Popen', side_effect=self._start_child) as spawn:
                with self.assertRaisesRegex(TimeoutError, 'command timed out'):
                    self.run_readonly(command, timeout=0.2)
        validate.assert_called_once_with(command)
        self.assertEqual(len(self.children), 1)
        process = self.children[0]
        self.assertIsNotNone(process.poll())
        self.assertLess(process.returncode, 0)
        self.assertTrue(process.stdout.closed)
        self.assertEqual(spawn.call_args.args[0], command)
        self.assertIs(spawn.call_args.kwargs['shell'], False)


if __name__ == '__main__':
    unittest.main()
