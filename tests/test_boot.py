"""
boot_offset.py的单元测试脚本
测试boot偏移号获取功能
"""
import unittest
from unittest.mock import patch, MagicMock
import sys
import os, runpy
import importlib.util
import subprocess
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
BOOT_PATH = os.path.join(PROJECT_ROOT, 'osmanager', 'system_log', 'manager-script', 'boot_offset.py')
sys.path.insert(0, PROJECT_ROOT)

def load_module_from(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod
LOG_PATH = os.path.join(PROJECT_ROOT, 'osmanager', 'system_log', 'manager-script', 'boot_offset.py')
boot_mod = load_module_from(LOG_PATH, 'osmanager.system_log.manager_script.boot_offset')
list_boot_offsets = boot_mod.list_boot_offsets

def _stream_text(mock_stream):
    return ''.join((call.args[0] for call in mock_stream.write.call_args_list))

class TestBootOffset(unittest.TestCase):
    """测试boot偏移号功能"""

    @patch('subprocess.run')
    def test_list_boot_offsets_success(self, mock_run):
        """测试成功获取boot偏移号列表"""
        mock_output = '0 12345678-1234-1234-1234-123456789abc Mon 2025-01-01 10:00:00 CST—Mon 2025-01-01 12:00:00 CST\n1 87654321-4321-4321-4321-cba987654321 Mon 2025-01-01 08:00:00 CST—Mon 2025-01-01 10:00:00 CST\n2 abcdef12-3456-7890-abcd-ef1234567890 Sun 2024-12-31 20:00:00 CST—Mon 2025-01-01 08:00:00 CST\n'
        mock_run.return_value = MagicMock(returncode=0, stdout=mock_output, stderr='')
        result = list_boot_offsets()
        expected = [0, 1, 2]
        self.assertEqual(result, expected)

    @patch('subprocess.run')
    def test_list_boot_offsets_empty(self, mock_run):
        """测试boot偏移号空输出情况"""
        mock_run.return_value = MagicMock(returncode=0, stdout='', stderr='')
        result = list_boot_offsets()
        self.assertEqual(result, [])

    @patch('subprocess.run')
    def test_list_boot_offsets_with_blank_lines(self, mock_run):
        """测试包含空行的情况"""
        mock_output = '0 12345678-1234-1234-1234-123456789abc Mon 2025-01-01 10:00:00 CST—Mon 2025-01-01 12:00:00 CST\n\n1 87654321-4321-4321-4321-cba987654321 Mon 2025-01-01 08:00:00 CST—Mon 2025-01-01 10:00:00 CST\n\n'
        mock_run.return_value = MagicMock(returncode=0, stdout=mock_output, stderr='')
        result = list_boot_offsets()
        expected = [0, 1]
        self.assertEqual(result, expected)

    @patch('subprocess.run')
    def test_list_boot_offsets_invalid_lines(self, mock_run):
        """测试包含无效行的情况"""
        mock_output = '0 12345678-1234-1234-1234-123456789abc Mon 2025-01-01 10:00:00 CST—Mon 2025-01-01 12:00:00 CST\ninvalid line\n1 87654321-4321-4321-4321-cba987654321 Mon 2025-01-01 08:00:00 CST—Mon 2025-01-01 10:00:00 CST\nanother invalid line\n2 abcdef12-3456-7890-abcd-ef1234567890 Sun 2024-12-31 20:00:00 CST—Mon 2025-01-01 08:00:00 CST\n'
        mock_run.return_value = MagicMock(returncode=0, stdout=mock_output, stderr='')
        result = list_boot_offsets()
        expected = [0, 1, 2]
        self.assertEqual(result, expected)

    @patch('subprocess.run')
    def test_list_boot_offsets_subprocess_error(self, mock_run):
        """测试subprocess执行错误"""
        mock_run.side_effect = subprocess.CalledProcessError(1, 'journalctl', stderr='Permission denied')
        result = list_boot_offsets()
        self.assertEqual(result, [])

    @patch('subprocess.run')
    def test_list_boot_offsets_subprocess_error_with_stderr(self, mock_run):
        import subprocess
        mock_run.side_effect = subprocess.CalledProcessError(1, 'journalctl', stderr='Permission denied')
        with patch('sys.stderr') as mock_stderr:
            result = list_boot_offsets()
            self.assertEqual(result, [])
            out = _stream_text(mock_stderr)
            self.assertEqual(out, 'Permission denied\n')

    def test_list_boot_offsets_environment(self):
        """测试环境变量设置"""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout='', stderr='')
            list_boot_offsets()
            call_kwargs = mock_run.call_args[1]
            env = call_kwargs['env']
            self.assertEqual(env['SYSTEMD_COLORS'], '0')
            self.assertIn('SYSTEMD_COLORS', env)

    def test_list_boot_offsets_command_args(self):
        """测试命令参数"""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout='', stderr='')
            list_boot_offsets()
            call_args = mock_run.call_args[0][0]
            expected_cmd = ['journalctl', '--no-pager', '--list-boots']
            self.assertEqual(call_args, expected_cmd)
            call_kwargs = mock_run.call_args[1]
            self.assertTrue(call_kwargs['capture_output'])
            self.assertTrue(call_kwargs['text'])
            self.assertTrue(call_kwargs['check'])

class TestBootOffsetMain(unittest.TestCase):

    def test_main_execution(self):
        mock_output = '0 aaaa Mon 2025-01-01 10:00:00—Mon 2025-01-01 12:00:00\n1 bbbb Mon 2025-01-01 08:00:00—Mon 2025-01-01 10:00:00\n2 cccc Sun 2024-12-31 20:00:00—Mon 2025-01-01 08:00:00\n'
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout=mock_output, stderr='')
            with patch('sys.stdout') as mock_stdout:
                runpy.run_path(BOOT_PATH, run_name='__main__')
                out = _stream_text(mock_stdout)
if __name__ == '__main__':
    unittest.main()
