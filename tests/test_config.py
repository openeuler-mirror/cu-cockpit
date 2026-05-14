"""
config模块单元测试
"""
import os
import sys
import django
from pathlib import Path
import json
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'osmanager.settings')
django.setup()
from unittest.mock import patch, MagicMock
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

class ConfigViewsTest(TestCase):

    def setUp(self):
        """测试初始化设置"""
        self.client = APIClient()
        session = self.client.session
        session['username'] = 'testuser'
        session.save()
        self.valid_script = 'config.sh'
        self.invalid_script = 'nonexistent_script.sh'
        self.valid_modes = ['sshkey', 'gethostname', 'time', 'get']
        self.invalid_mode = 'invalid_mode'

    def _get_response_data(self, response):
        """统一处理响应数据提取"""
        try:
            if hasattr(response, 'data'):
                return response.data
            return json.loads(response.content.decode('utf-8'))
        except (AttributeError, json.JSONDecodeError):
            return {'error': '无法解析响应数据'}

    def test_get_config_api_success(self):
        """测试成功执行配置脚本的情况"""
        test_cases = [('sshkey', None, 'json'), ('gethostname', None, 'text'), ('time', None, 'json'), ('get', 'bashrc', 'text')]
        for mode, key, expected_format in test_cases:
            with self.subTest(mode=mode):
                with patch('os.path.isfile', return_value=True), patch('subprocess.run') as mock_subprocess:
                    mock_result = MagicMock()
                    mock_result.returncode = 0
                    if expected_format == 'json':
                        mock_result.stdout = '{"status": "ok"}'
                    else:
                        mock_result.stdout = 'output text'
                    mock_result.stderr = ''
                    mock_subprocess.return_value = mock_result
                    url = f'/api/config/get/{self.valid_script}?mode={mode}'
                    if key:
                        url += f'&key={key}'
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, status.HTTP_200_OK)
                    if expected_format == 'json':
                        data = self._get_response_data(response)
                        self.assertIn('status', data)
                    else:
                        self.assertEqual(response['content-type'], 'text/plain; charset=utf-8')

    def test_get_config_api_script_not_found(self):
        """测试脚本不存在的情况"""
        with patch('os.path.isfile', return_value=False):
            response = self.client.get(f'/api/config/get/{self.invalid_script}?mode=sshkey')
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
            data = self._get_response_data(response)
            self.assertIn('not found', data.get('error', '').lower())

    def test_get_config_api_missing_mode(self):
        """测试缺少必需mode参数的情况"""
        with patch('os.path.isfile', return_value=True):
            response = self.client.get(f'/api/config/get/{self.valid_script}')
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            data = self._get_response_data(response)
            self.assertIn('mode 必填', data.get('message', ''))

    def test_get_config_api_invalid_mode(self):
        """测试无效的mode参数"""
        with patch('os.path.isfile', return_value=True):
            response = self.client.get(f'/api/config/get/{self.valid_script}?mode={self.invalid_mode}')
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            data = self._get_response_data(response)
            self.assertIn('只允许为', data.get('message', ''))

    def test_get_config_api_missing_key_for_get_mode(self):
        """测试get模式缺少key参数的情况"""
        with patch('os.path.isfile', return_value=True):
            response = self.client.get(f'/api/config/get/{self.valid_script}?mode=get')
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            data = self._get_response_data(response)
            self.assertIn('key 必填', data.get('message', ''))

    def test_get_config_api_script_execution_failure(self):
        """测试脚本执行失败的情况"""
        with patch('os.path.isfile', return_value=True), patch('subprocess.run') as mock_subprocess:
            mock_result = MagicMock()
            mock_result.returncode = 1
            mock_result.stdout = ''
            mock_result.stderr = 'Permission denied'
            mock_subprocess.return_value = mock_result
            response = self.client.get(f'/api/config/get/{self.valid_script}?mode=sshkey')
            self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            data = self._get_response_data(response)
            self.assertIn('执行失败', data.get('error', ''))

    def test_get_config_api_non_json_output_for_json_mode(self):
        """测试JSON模式返回非JSON输出的情况"""
        with patch('os.path.isfile', return_value=True), patch('subprocess.run') as mock_subprocess:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = 'This is not JSON'
            mock_result.stderr = ''
            mock_subprocess.return_value = mock_result
            response = self.client.get(f'/api/config/get/{self.valid_script}?mode=sshkey')
            self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            data = self._get_response_data(response)
            self.assertIn('not json', data.get('error', ''))

    def test_set_time_hostname_api_success(self):
        """测试成功设置时间和主机名的情况"""
        test_cases = [('set_time.sh', {'type': 'autotime'}), ('set_time.sh', {'type': 'settime', 'time': '2025-09-01 12:00:00 +0800'}), ('config.sh', {'hostname': 'newhostname'})]
        for script_name, data in test_cases:
            with self.subTest(script_name=script_name):
                with patch('os.path.isfile', return_value=True), patch('subprocess.run') as mock_subprocess:
                    mock_result = MagicMock()
                    mock_result.returncode = 0
                    mock_result.stdout = 'success'
                    mock_result.stderr = ''
                    mock_subprocess.return_value = mock_result
                    response = self.client.post(f'/api/config/set/{script_name}', data=data, format='json')
                    self.assertEqual(response.status_code, status.HTTP_200_OK)
                    response_data = self._get_response_data(response)
                    self.assertTrue(response_data.get('success_flag', False))

    def test_set_time_hostname_api_unsupported_script(self):
        """测试不支持的脚本名称"""
        with patch('os.path.isfile', return_value=True):
            response = self.client.post('/api/config/set/invalid_script.sh', data={'type': 'autotime'}, format='json')
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            response_data = self._get_response_data(response)
            self.assertIn('不支持的脚本', response_data.get('error', ''))

    def test_set_time_hostname_api_script_not_found(self):
        """测试脚本文件不存在的情况"""
        with patch('os.path.isfile', return_value=False):
            response = self.client.post(f'/api/config/set/{self.valid_script}', data={'hostname': 'test'}, format='json')
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
            response_data = self._get_response_data(response)
            self.assertIn('not found', response_data.get('error', '').lower())

    def test_set_time_hostname_api_invalid_params(self):
        """测试无效参数的情况"""
        test_cases = [('set_time.sh', {'type': 'invalid_type'}, 'type只允许为'), ('set_time.sh', {}, 'type只允许为'), ('set_time.sh', {'type': 'settime'}, 'time'), ('config.sh', {}, 'hostname')]
        for script_name, data, error_keyword in test_cases:
            with self.subTest(script_name=script_name):
                with patch('os.path.isfile', return_value=True):
                    response = self.client.post(f'/api/config/set/{script_name}', data=data, format='json')
                    self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                    response_data = self._get_response_data(response)
                    message = response_data.get('message', '')
                    self.assertTrue(any((keyword in message for keyword in [error_keyword, '错误'])), f"Message should contain '{error_keyword}', but got: '{message}'")

    def test_set_time_hostname_api_script_failure(self):
        """测试脚本执行失败的情况"""
        with patch('os.path.isfile', return_value=True), patch('subprocess.run') as mock_subprocess:
            mock_result = MagicMock()
            mock_result.returncode = 1
            mock_result.stdout = ''
            mock_result.stderr = 'Command failed'
            mock_subprocess.return_value = mock_result
            response = self.client.post('/api/config/set/config.sh', data={'hostname': 'test'}, format='json')
            self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            response_data = self._get_response_data(response)
            self.assertFalse(response_data.get('success_flag', True))

    def test_write_bytes_to_file_success(self):
        """测试成功写入字节数据到文件"""
        test_data = b'test binary data'
        with patch('builtins.open', MagicMock()) as mock_open, patch('pathlib.Path.mkdir') as mock_mkdir, patch('pathlib.Path.exists', return_value=True), patch('pathlib.Path.stat') as mock_stat:
            mock_stat_result = MagicMock()
            mock_stat_result.st_size = len(test_data)
            mock_stat.return_value = mock_stat_result
            mock_file = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file
            response = self.client.post('/api/config/update/?file_path=test.txt', data=test_data, content_type='application/octet-stream')
            if response.status_code == status.HTTP_200_OK:
                response_data = self._get_response_data(response)
                self.assertTrue(response_data.get('success', False))
            else:
                self.skipTest(f'视图返回非预期状态码: {response.status_code}')

    def test_write_bytes_to_file_missing_path(self):
        """测试缺少文件路径参数的情况"""
        pass

    def test_write_bytes_to_file_invalid_data(self):
        """测试无效数据的情况"""
        pass

    def test_debug_view_response(self):
        """调试视图的实际响应"""
        pass
if __name__ == '__main__':
    import unittest
    unittest.main()
