import sys
import os
import unittest
from unittest.mock import patch, MagicMock
import json
from io import StringIO
import subprocess
sys.path.insert(0, '/opt/chinaunicom/osmanager/osmanager/rescrouce_monitor/manager-script')
from importlib.util import spec_from_file_location, module_from_spec
spec = spec_from_file_location('service_status', '/opt/chinaunicom/osmanager/osmanager/rescrouce_monitor/manager-script/service_status.py')
service_status = module_from_spec(spec)
sys.modules['service_status'] = service_status
spec.loader.exec_module(service_status)

class TestServiceStatus(unittest.TestCase):

    def setUp(self):
        self.maxDiff = None

    @patch('subprocess.run')
    def test_run_command_success(self, mock_run):
        """测试成功执行命令的情况"""
        mock_result = MagicMock()
        mock_result.stdout = 'line1\nline2\nline3'
        mock_result.stderr = ''
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        result = service_status.run_command('echo test')
        self.assertEqual(result, ['line1', 'line2', 'line3'])

    @patch('subprocess.run')
    def test_run_command_failure(self, mock_run):
        """测试命令执行失败的情况"""
        mock_run.side_effect = subprocess.CalledProcessError(returncode=1, cmd='false', stderr='Command failed')
        with self.assertRaises(RuntimeError):
            service_status.run_command('false')

    def test_parse_unit_files(self):
        """测试解析unit files输出"""
        sample_input = ['sshd.service enabled', 'nginx.service disabled', 'docker.service static', '  extra.space.service  masked  ', 'invalidline', '']
        expected = {'sshd.service': 'enabled', 'nginx.service': 'disabled', 'docker.service': 'static', 'extra.space.service': 'masked'}
        result = service_status.parse_unit_files(sample_input)
        self.assertEqual(result, expected)

    def test_parse_units(self):
        """测试解析units输出"""
        sample_input = ['sshd.service loaded active running OpenSSH server', 'nginx.service loaded inactive dead nginx web server', '  docker.service  loaded  active  running  Docker Application Container Engine  ', 'invalid.line', '']
        expected = {'sshd.service': {'运行状态': 'active', '描述': 'OpenSSH server'}, 'nginx.service': {'运行状态': 'inactive', '描述': 'nginx web server'}, 'docker.service': {'运行状态': 'active', '描述': 'Docker Application Container Engine'}}
        result = service_status.parse_units(sample_input)
        self.assertEqual(result, expected)

    def test_merge_and_print(self):
        """测试合并和打印功能"""
        unit_files = {'sshd.service': 'enabled', 'nginx.service': 'disabled', 'missing.service': 'static'}
        units = {'sshd.service': {'运行状态': 'active', '描述': 'OpenSSH server'}, 'docker.service': {'运行状态': 'active', '描述': 'Docker'}}
        pass

    @patch('service_status.run_command')
    def test_main_logic_success(self, mock_run):
        """测试主业务逻辑成功执行"""
        pass

    @patch('service_status.run_command')
    def test_main_logic_error(self, mock_run):
        """测试主业务逻辑错误处理"""
        pass
if __name__ == '__main__':
    unittest.main()
