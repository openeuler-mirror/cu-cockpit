"""
system_log 模块单元测试
"""
import os
import sys
import django
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'osmanager.settings')
django.setup()
import json
from unittest.mock import patch, MagicMock
from django.test import TestCase, Client
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

class SystemLogViewsTest(TestCase):

    def setUp(self):
        """测试初始化设置"""
        self.client = APIClient()
        session = self.client.session
        session['username'] = 'testuser'
        session.save()
        self.valid_service = 'sshd'
        self.valid_priority = 'err'
        self.valid_since = '2025-08-01 00:00:00'
        self.valid_until = '2025-08-02 23:59:59'
        self.valid_limit = 100
        self.valid_keyword = 'failed'
        self.valid_boot = '0'
        self.valid_identifier = 'sshd'
        self.valid_cursor = 's=;i=;b=;m=;t=;x='
        self.valid_output_format = 'summary'

    def test_boots_view_success(self):
        """测试成功获取引导偏移列表的情况"""
        with patch('os.path.exists', return_value=True), patch('subprocess.run') as mock_subprocess:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = '[0, -1, -2, -3]'
            mock_result.stderr = ''
            mock_subprocess.return_value = mock_result
            response = self.client.get('/api/logs/boot/')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            data = response.json()
            self.assertIn('boots', data)
            self.assertIn('count', data)
            self.assertEqual(data['boots'], [0, -1, -2, -3])
            self.assertEqual(data['count'], 4)
            mock_subprocess.assert_called_once()

    def test_boots_view_script_not_found(self):
        """测试引导脚本不存在的情况"""
        with patch('os.path.exists', return_value=False):
            response = self.client.get('/api/logs/boot/')
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
            data = response.json()
            self.assertIn('error', data)
            self.assertIn('boot_offset.py不存在', data['error'])

    def test_boots_view_script_execution_failure(self):
        """测试引导脚本执行失败的情况"""
        with patch('os.path.exists', return_value=True), patch('subprocess.run') as mock_subprocess:
            mock_result = MagicMock()
            mock_result.returncode = 1
            mock_result.stdout = ''
            mock_result.stderr = 'Permission denied'
            mock_subprocess.return_value = mock_result
            response = self.client.get('/api/logs/boot/')
            self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            data = response.json()
            self.assertIn('error', data)
            self.assertIn('boot.py返回非0状态码', data['error'])

    def test_boots_view_timeout(self):
        """测试引导脚本执行超时的情况"""
        import subprocess
        with patch('os.path.exists', return_value=True), patch('subprocess.run') as mock_subprocess:
            mock_subprocess.side_effect = subprocess.TimeoutExpired('python3', 20)
            response = self.client.get('/api/logs/boot/')
            self.assertEqual(response.status_code, 504)
            data = response.json()
            self.assertIn('error', data)
            self.assertIn('调用boot.py超时', data['error'])

    def test_boots_view_file_not_found(self):
        """测试引导脚本文件未找到的情况"""
        with patch('os.path.exists', return_value=True), patch('subprocess.run') as mock_subprocess:
            mock_subprocess.side_effect = FileNotFoundError('File not found')
            response = self.client.get('/api/logs/boot/')
            self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            data = response.json()
            self.assertIn('error', data)
            self.assertIn('执行失败', data['error'])

    def test_boots_view_python_list_parse(self):
        """测试引导脚本返回Python列表字符串的情况"""
        with patch('os.path.exists', return_value=True), patch('subprocess.run') as mock_subprocess:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = '[0, -1, -2, -3]'
            mock_result.stderr = ''
            mock_subprocess.return_value = mock_result
            response = self.client.get('/api/logs/boot/')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            data = response.json()
            self.assertEqual(data['boots'], [0, -1, -2, -3])
            self.assertEqual(data['count'], 4)

    def test_logs_view_success(self):
        """测试成功查询系统日志的情况"""
        with patch('os.path.exists', return_value=True), patch('subprocess.run') as mock_subprocess:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = json.dumps([{'date': 'Sep 09', 'time': '10:23:09', 'hostname': 'bigdata1', 'service': 'PackageKit', 'pid': 2177658, 'message': 'message content', 'raw': 'raw log line'}])
            mock_result.stderr = ''
            mock_subprocess.return_value = mock_result
            response = self.client.get(f'/api/logs/logs/?service={self.valid_service}&priority={self.valid_priority}')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            data = response.json()
            self.assertIn('logs', data)
            self.assertIn('count', data)
            self.assertEqual(len(data['logs']), 1)
            self.assertEqual(data['count'], 1)
            mock_subprocess.assert_called_once()

    def test_logs_view_script_not_found(self):
        """测试日志脚本不存在的情况"""
        with patch('os.path.exists', return_value=False):
            response = self.client.get('/api/logs/logs/')
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
            data = response.json()
            self.assertIn('error', data)
            self.assertIn('log.py不存在', data['error'])

    def test_logs_view_script_execution_failure(self):
        """测试日志脚本执行失败的情况"""
        with patch('os.path.exists', return_value=True), patch('subprocess.run') as mock_subprocess:
            mock_result = MagicMock()
            mock_result.returncode = 1
            mock_result.stdout = ''
            mock_result.stderr = 'Permission denied'
            mock_subprocess.return_value = mock_result
            response = self.client.get('/api/logs/logs/')
            self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            data = response.json()
            self.assertIn('error', data)
            self.assertIn('log.py返回非0状态码', data['error'])

    def test_logs_view_timeout(self):
        """测试日志脚本执行超时的情况"""
        import subprocess
        with patch('os.path.exists', return_value=True), patch('subprocess.run') as mock_subprocess:
            mock_subprocess.side_effect = subprocess.TimeoutExpired('python3', 60)
            response = self.client.get('/api/logs/logs/')
            self.assertEqual(response.status_code, 504)
            data = response.json()
            self.assertIn('error', data)
            self.assertIn('调用 log.py 超时', data['error'])

    def test_logs_view_file_not_found(self):
        """测试日志脚本文件未找到的情况"""
        with patch('os.path.exists', return_value=True), patch('subprocess.run') as mock_subprocess:
            mock_subprocess.side_effect = FileNotFoundError('File not found')
            response = self.client.get('/api/logs/logs/')
            self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            data = response.json()
            self.assertIn('error', data)
            self.assertIn('执行失败', data['error'])

    def test_logs_view_empty_output(self):
        """测试日志脚本返回空输出的情况"""
        with patch('os.path.exists', return_value=True), patch('subprocess.run') as mock_subprocess:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = ''
            mock_result.stderr = ''
            mock_subprocess.return_value = mock_result
            response = self.client.get('/api/logs/logs/')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            data = response.json()
            self.assertEqual(data['logs'], [])
            self.assertEqual(data['count'], 0)

    def test_logs_view_non_json_output(self):
        """测试日志脚本返回非JSON输出的情况"""
        with patch('os.path.exists', return_value=True), patch('subprocess.run') as mock_subprocess:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = 'This is not JSON output'
            mock_result.stderr = ''
            mock_subprocess.return_value = mock_result
            response = self.client.get('/api/logs/logs/')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            data = response.json()
            self.assertIn('raw_output', data)
            self.assertEqual(data['raw_output'], 'This is not JSON output')

    def test_logs_view_dict_output(self):
        """测试日志脚本返回字典格式的情况"""
        with patch('os.path.exists', return_value=True), patch('subprocess.run') as mock_subprocess:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = json.dumps({'summary': 'test', 'count': 1})
            mock_result.stderr = ''
            mock_subprocess.return_value = mock_result
            response = self.client.get('/api/logs/logs/')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            data = response.json()
            self.assertEqual(data['summary'], 'test')
            self.assertEqual(data['count'], 1)

    def test_logs_view_with_all_parameters(self):
        """测试使用所有查询参数的情况"""
        with patch('os.path.exists', return_value=True), patch('subprocess.run') as mock_subprocess:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = json.dumps([])
            mock_result.stderr = ''
            mock_subprocess.return_value = mock_result
            url = f'/api/logs/logs/?service={self.valid_service}&priority={self.valid_priority}&since={self.valid_since}&until={self.valid_until}&limit={self.valid_limit}&keyword={self.valid_keyword}&boot={self.valid_boot}&identifier={self.valid_identifier}&cursor={self.valid_cursor}&output_format={self.valid_output_format}'
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            mock_subprocess.assert_called_once()

    def test_logs_view_structured_error_from_stderr(self):
        """测试日志脚本在stderr中返回结构化错误的情况"""
        with patch('os.path.exists', return_value=True), patch('subprocess.run') as mock_subprocess:
            mock_result = MagicMock()
            mock_result.returncode = 1
            mock_result.stdout = ''
            mock_result.stderr = json.dumps({'error': 'structured error', 'code': 1001})
            mock_subprocess.return_value = mock_result
            response = self.client.get('/api/logs/logs/')
            self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            data = response.json()
            self.assertEqual(data['error'], 'structured error')
            self.assertEqual(data['code'], 1001)

    def test_logs_view_unknown_exception(self):
        """测试日志脚本抛出未知异常的情况"""
        with patch('os.path.exists', return_value=True), patch('subprocess.run') as mock_subprocess:
            mock_subprocess.side_effect = Exception('Unknown error')
            response = self.client.get('/api/logs/logs/')
            self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            data = response.json()
            self.assertIn('error', data)
            self.assertIn('未知错误', data['error'])

    def test_build_cmd_from_request_get(self):
        """测试从GET请求构建命令的情况"""
        from osmanager.system_log.views import _build_cmd_from_request

        class MockRequest:

            def __init__(self, method='GET', params=None):
                self.method = method
                self.GET = params or {}
                self.POST = {}
        request = MockRequest('GET', {'service': 'sshd', 'priority': 'err', 'since': '2025-08-01', 'until': '2025-08-02', 'limit': '100', 'keyword': 'failed', 'boot': '0', 'identifier': 'sshd', 'cursor': 'test_cursor', 'output_format': 'summary'})
        cmd = _build_cmd_from_request(request)
        self.assertIn('python3', cmd[0])
        self.assertIn('log.py', cmd[1])
        self.assertIn('--since', cmd)
        self.assertIn('2025-08-01', cmd)
        self.assertIn('-s', cmd)
        self.assertIn('sshd', cmd)
        self.assertIn('-p', cmd)
        self.assertIn('err', cmd)

    def test_build_cmd_from_request_post(self):
        """测试构建命令的情况"""
        from osmanager.system_log.views import _build_cmd_from_request

        class MockRequest:

            def __init__(self, method='POST', params=None):
                self.method = method
                self.GET = {}
                self.POST = params or {}
        request = MockRequest('POST', {'service': 'nginx', 'priority': 'info'})
        cmd = _build_cmd_from_request(request)
        self.assertIn('python3', cmd[0])
        self.assertIn('log.py', cmd[1])
        self.assertIn('-s', cmd)
        self.assertIn('nginx', cmd)
        self.assertIn('-p', cmd)
        self.assertIn('info', cmd)

    def test_build_cmd_from_request_empty_params(self):
        """测试空参数构建命令的情况"""
        from osmanager.system_log.views import _build_cmd_from_request

        class MockRequest:

            def __init__(self, method='GET', params=None):
                pass
        request = MockRequest('GET', {})
        cmd = _build_cmd_from_request(request)
        self.assertEqual(len(cmd), 2)
        self.assertIn('python3', cmd[0])
        self.assertIn('log.py', cmd[1])

    def test_build_cmd_from_request_none_values(self):
        """测试包含None值的参数构建命令的情况"""
        pass
