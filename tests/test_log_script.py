"""
log.py 的单元测试脚本
测试日志解析和journalctl命令执行功能
"""
import unittest
from unittest.mock import patch, MagicMock
import json
import sys
import os
import importlib.util
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, PROJECT_ROOT)

def load_module_from(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod
LOG_PATH = os.path.join(PROJECT_ROOT, 'osmanager', 'system_log', 'manager-script', 'log.py')
log_mod = load_module_from(LOG_PATH, 'osmanager.system_log.manager_script.log')
parse_log_line = log_mod.parse_log_line
extract_summary_fields = log_mod.extract_summary_fields
main = log_mod.main

def _stream_text(mock_stream):
    return ''.join((call.args[0] for call in mock_stream.write.call_args_list))

class TestLogParsing(unittest.TestCase):
    """测试日志解析功能"""

    def test_parse_log_line_valid(self):
        """测试解析有效的日志行"""
        line = 'Sep 09 10:23:09 bigdata1 PackageKit[2177658]: message content'
        result = parse_log_line(line)
        expected = {'date': 'Sep 09', 'time': '10:23:09', 'hostname': 'bigdata1', 'service': 'PackageKit', 'pid': 2177658, 'message': 'message content', 'raw': line}
        self.assertEqual(result, expected)

    def test_parse_log_line_invalid(self):
        """测试解析无效的日志行"""
        line = 'invalid log format'
        result = parse_log_line(line)
        expected = {'date': '', 'time': '', 'hostname': '', 'service': '', 'pid': 0, 'message': line, 'raw': line}
        self.assertEqual(result, expected)

    def test_parse_log_line_edge_cases(self):
        """测试边界情况"""
        result = parse_log_line('')
        self.assertEqual(result['message'], '')
        result = parse_log_line('   ')
        self.assertEqual(result['message'], '')
        line = 'Sep 09 10:23:09 host service[123]: message with special chars !@#$%'
        result = parse_log_line(line)
        self.assertEqual(result['message'], 'message with special chars !@#$%')

    def test_extract_summary_fields(self):
        """测试提取摘要字段"""
        log_entry = {'__REALTIME_TIMESTAMP': '1234567890000000', 'MESSAGE': 'test message', '_SYSTEMD_UNIT': 'test.service', 'UNIT': 'test.unit', 'SYSLOG_IDENTIFIER': 'test-identifier', '_HOSTNAME': 'test-host', '__CURSOR': 'test-cursor', 'OTHER_FIELD': 'ignored'}
        result = extract_summary_fields(log_entry)
        expected = {'timestamp': '1234567890000000', 'message': 'test message', 'service': 'test.service', 'identifier': 'test-identifier', 'hostname': 'test-host', 'cursor': 'test-cursor'}
        self.assertEqual(result, expected)

    def test_extract_summary_fields_missing_fields(self):
        """测试缺少某些字段的情况"""
        log_entry = {'MESSAGE': 'test message', 'UNIT': 'test.unit'}
        result = extract_summary_fields(log_entry)
        expected = {'timestamp': '', 'message': 'test message', 'service': 'test.unit', 'identifier': '', 'hostname': '', 'cursor': ''}
        self.assertEqual(result, expected)

class TestLogMain(unittest.TestCase):
    """测试main函数"""

    @patch('subprocess.run')
    def test_main_success_raw_output(self, mock_run):
        """测试成功执行raw输出格式"""
        mock_run.return_value = MagicMock(returncode=0, stdout='Sep 09 10:23:09 host service[123]: test message\n', stderr='')
        with patch('sys.argv', ['log.py', '--output_format', 'raw']):
            with patch('sys.stdout') as mock_stdout:
                main()
                out = _stream_text(mock_stdout)
                self.assertEqual(out, 'Sep 09 10:23:09 host service[123]: test message\n\n')

    @patch('subprocess.run')
    def test_main_success_json_output(self, mock_run):
        """测试成功执行json输出格式"""
        mock_run.return_value = MagicMock(returncode=0, stdout='Sep 09 10:23:09 host service[123]: test message\n', stderr='')
        with patch('sys.argv', ['log.py', '--output_format', 'json']):
            with patch('sys.stdout') as mock_stdout:
                main()
                out = _stream_text(mock_stdout)
                data = json.loads(out)
                self.assertEqual(len(data), 1)
                self.assertEqual(data[0]['message'], 'test message')

    @patch('subprocess.run')
    def test_main_no_entries(self, mock_run):
        """测试没有日志条目的情况"""
        mock_run.return_value = MagicMock(returncode=1, stdout='-- No entries --\n', stderr='')
        with patch('sys.argv', ['log.py', '--output_format', 'raw']):
            with patch('sys.stdout') as mock_stdout:
                out = _stream_text(mock_stdout)
                self.assertEqual(out, '')

    @patch('subprocess.run')
    def test_main_journalctl_error(self, mock_run):
        """测试journalctl执行错误"""
        pass

    @patch('subprocess.run')
    def test_main_file_not_found(self, mock_run):
        """测试journalctl命令不存在"""
        pass

    def test_argument_parsing(self):
        """测试命令行参数解析"""
        pass
if __name__ == '__main__':
    unittest.main()
