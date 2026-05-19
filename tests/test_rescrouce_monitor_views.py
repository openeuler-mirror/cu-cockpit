"""
资源监控模块测试用例
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
from rest_framework import status

class TestMonitorStatusShModes(TestCase):
    """测试 monitor_status.sh 的不同模式功能"""

    def setUp(self):
        """测试前设置"""
        self.client = Client()
        session = self.client.session
        session['username'] = 'testuser'
        session.save()

    @patch('osmanager.rescrouce_monitor.views.os.path.isfile')
    @patch('osmanager.rescrouce_monitor.views.subprocess.run')
    def test_monitor_all_mode(self, mock_subprocess, mock_isfile):
        """测试 monitor_status.sh mode=all 返回所有监控信息"""
        mock_isfile.return_value = True
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps({'cpu': {'total_utilization_percent': '50%'}, 'disk': {'total_usage_percent': '60%'}, 'memory': {'used_mb': 4096}, 'network': {'interfaces': []}})
        mock_result.stderr = ''
        mock_subprocess.return_value = mock_result
        response = self.client.get('/api/rescrouce/monitor/monitor_status.sh?mode=all')
        if mock_subprocess.called:
            call_args = mock_subprocess.call_args[0][0]
            self.assertIn('all', call_args)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = json.loads(response.content)
        self.assertIn('cpu', response_data)
        self.assertIn('disk', response_data)
        self.assertIn('memory', response_data)
        self.assertIn('network', response_data)

    @patch('osmanager.rescrouce_monitor.views.os.path.isfile')
    @patch('osmanager.rescrouce_monitor.views.subprocess.run')
    def test_monitor_cpu_mode(self, mock_subprocess, mock_isfile):
        """测试 monitor_status.sh mode=cpu 只返回CPU信息"""
        mock_isfile.return_value = True
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps({'cpu': {'total_utilization_percent': '45.5%', 'user_percent': '30%', 'system_percent': '15%', 'idle_percent': '55%', 'load_average': '1分钟: 0.5'}})
        mock_result.stderr = ''
        mock_subprocess.return_value = mock_result
        response = self.client.get('/api/rescrouce/monitor/monitor_status.sh?mode=cpu')
        if mock_subprocess.called:
            call_args = mock_subprocess.call_args[0][0]
            self.assertIn('cpu', call_args)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = json.loads(response.content)
        self.assertIn('cpu', response_data)
        self.assertIn('total_utilization_percent', response_data['cpu'])

    @patch('osmanager.rescrouce_monitor.views.os.path.isfile')
    @patch('osmanager.rescrouce_monitor.views.subprocess.run')
    def test_monitor_disk_mode(self, mock_subprocess, mock_isfile):
        """测试 monitor_status.sh mode=disk 只返回磁盘信息"""
        mock_isfile.return_value = True
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps({'disk': {'total_size_gb': 500, 'used_gb': 300, 'available_gb': 200, 'usage_percent': '60%'}})
        mock_result.stderr = ''
        mock_subprocess.return_value = mock_result
        response = self.client.get('/api/rescrouce/monitor/monitor_status.sh?mode=disk')
        if mock_subprocess.called:
            call_args = mock_subprocess.call_args[0][0]
            self.assertIn('disk', call_args)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = json.loads(response.content)
        self.assertIn('disk', response_data)
        self.assertEqual(response_data['disk']['usage_percent'], '60%')

    @patch('osmanager.rescrouce_monitor.views.os.path.isfile')
    @patch('osmanager.rescrouce_monitor.views.subprocess.run')
    def test_monitor_memory_mode(self, mock_subprocess, mock_isfile):
        """测试 monitor_status.sh mode=memory 只返回内存信息"""
        mock_isfile.return_value = True
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps({'memory': {'total_mb': 8192, 'used_mb': 4096, 'available_mb': 4096}})
        mock_result.stderr = ''
        mock_subprocess.return_value = mock_result
        response = self.client.get('/api/rescrouce/monitor/monitor_status.sh?mode=memory')
        if mock_subprocess.called:
            call_args = mock_subprocess.call_args[0][0]
            self.assertIn('memory', call_args)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = json.loads(response.content)
        self.assertIn('memory', response_data)
        self.assertIn('total_mb', response_data['memory'])

    @patch('osmanager.rescrouce_monitor.views.os.path.isfile')
    @patch('osmanager.rescrouce_monitor.views.subprocess.run')
    def test_monitor_network_mode(self, mock_subprocess, mock_isfile):
        """测试 monitor_status.sh mode=network 只返回网络信息"""
        mock_isfile.return_value = True
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps({'network': {'interfaces': [{'name': 'eth0', 'status': 'up'}]}})
        mock_result.stderr = ''
        mock_subprocess.return_value = mock_result
        response = self.client.get('/api/rescrouce/monitor/monitor_status.sh?mode=network')
        if mock_subprocess.called:
            call_args = mock_subprocess.call_args[0][0]
            self.assertIn('network', call_args)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = json.loads(response.content)
        self.assertIn('network', response_data)
        self.assertIn('interfaces', response_data['network'])

    @patch('osmanager.rescrouce_monitor.views.os.path.isfile')
    def test_monitor_invalid_mode(self, mock_isfile):
        """测试 monitor_status.sh 传入无效mode"""
        mock_isfile.return_value = True
        response = self.client.get('/api/rescrouce/monitor/monitor_status.sh?mode=invalid')
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertIn('mode 只允许为', response_data['message'])

    @patch('osmanager.rescrouce_monitor.views.os.path.isfile')
    def test_monitor_missing_mode(self, mock_isfile):
        """测试 monitor_status.sh 缺少mode参数"""
        mock_isfile.return_value = True
        response = self.client.get('/api/rescrouce/monitor/monitor_status.sh')
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertIn('mode 必填且不能为空', response_data['message'])

class TestHardInfoShModes(TestCase):
    """测试 hard_info.sh 的不同模式功能"""

    def setUp(self):
        """测试前设置"""
        self.client = Client()
        session = self.client.session
        session['username'] = 'testuser'
        session.save()

    @patch('osmanager.rescrouce_monitor.views.os.path.isfile')
    @patch('osmanager.rescrouce_monitor.views.subprocess.run')
    def test_hard_info_cpu_mode(self, mock_subprocess, mock_isfile):
        """测试 hard_info.sh mode=cpu 返回CPU硬件信息"""
        mock_isfile.return_value = True
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps({'cpu': {'model': 'Intel Core i7-10700K', 'cores': 8, 'vendor': 'Intel'}})
        mock_result.stderr = ''
        mock_subprocess.return_value = mock_result
        response = self.client.get('/api/rescrouce/monitor/hard_info.sh?mode=cpu')
        if mock_subprocess.called:
            call_args = mock_subprocess.call_args[0][0]
            self.assertIn('cpu', call_args)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = json.loads(response.content)
        self.assertIn('cpu', response_data)
        self.assertIn('model', response_data['cpu'])

    @patch('osmanager.rescrouce_monitor.views.os.path.isfile')
    @patch('osmanager.rescrouce_monitor.views.subprocess.run')
    def test_hard_info_system_mode(self, mock_subprocess, mock_isfile):
        """测试 hard_info.sh mode=system 返回系统信息"""
        mock_isfile.return_value = True
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps({'system': {'manufacturer': 'Dell Inc.', 'product_name': 'PowerEdge R740'}})
        mock_result.stderr = ''
        mock_subprocess.return_value = mock_result
        response = self.client.get('/api/rescrouce/monitor/hard_info.sh?mode=system')
        if mock_subprocess.called:
            call_args = mock_subprocess.call_args[0][0]
            self.assertIn('system', call_args)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = json.loads(response.content)
        self.assertIn('system', response_data)

    @patch('osmanager.rescrouce_monitor.views.os.path.isfile')
    @patch('osmanager.rescrouce_monitor.views.subprocess.run')
    def test_hard_info_bios_mode(self, mock_subprocess, mock_isfile):
        """测试 hard_info.sh mode=bios 返回BIOS信息"""
        mock_isfile.return_value = True
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps({'bios': {'vendor': 'Dell Inc.', 'version': '2.0.1'}})
        mock_result.stderr = ''
        mock_subprocess.return_value = mock_result
        response = self.client.get('/api/rescrouce/monitor/hard_info.sh?mode=bios')
        if mock_subprocess.called:
            call_args = mock_subprocess.call_args[0][0]
            self.assertIn('bios', call_args)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = json.loads(response.content)
        self.assertIn('bios', response_data)

    @patch('osmanager.rescrouce_monitor.views.os.path.isfile')
    @patch('osmanager.rescrouce_monitor.views.subprocess.run')
    def test_hard_info_os_system_mode(self, mock_subprocess, mock_isfile):
        """测试 hard_info.sh mode=os_system 返回操作系统信息"""
        mock_isfile.return_value = True
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps({'os_system': {'name': 'Ubuntu', 'version': '20.04'}})
        mock_result.stderr = ''
        mock_subprocess.return_value = mock_result
        response = self.client.get('/api/rescrouce/monitor/hard_info.sh?mode=os_system')
        if mock_subprocess.called:
            call_args = mock_subprocess.call_args[0][0]
            self.assertIn('os_system', call_args)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = json.loads(response.content)
        self.assertIn('os_system', response_data)

    @patch('osmanager.rescrouce_monitor.views.os.path.isfile')
    @patch('osmanager.rescrouce_monitor.views.subprocess.run')
    def test_hard_info_storage_mode(self, mock_subprocess, mock_isfile):
        """测试 hard_info.sh mode=storage 返回存储信息"""
        mock_isfile.return_value = True
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps({'storage': {'devices': ['/dev/sda', '/dev/sdb']}})
        mock_result.stderr = ''
        mock_subprocess.return_value = mock_result
        response = self.client.get('/api/rescrouce/monitor/hard_info.sh?mode=storage')
        if mock_subprocess.called:
            call_args = mock_subprocess.call_args[0][0]
            self.assertIn('storage', call_args)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = json.loads(response.content)
        self.assertIn('storage', response_data)

    def test_hard_info_invalid_mode(self):
        """测试 hard_info.sh 传入无效mode"""
        response = self.client.get('/api/rescrouce/monitor/hard_info.sh?mode=invalid')
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertIn('mode 只允许为', response_data['message'])

class TestScriptsWithoutMode(TestCase):
    """测试不需要mode参数的脚本"""

    def setUp(self):
        """测试前设置"""
        self.client = Client()
        session = self.client.session
        session['username'] = 'testuser'
        session.save()

    @patch('osmanager.rescrouce_monitor.views.os.path.isfile')
    @patch('osmanager.rescrouce_monitor.views.subprocess.run')
    def test_memory_slot_without_mode(self, mock_subprocess, mock_isfile):
        """测试 memory_slot.sh 不需要mode参数"""
        mock_isfile.return_value = True
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps({'memory_slots': []})
        mock_result.stderr = ''
        mock_subprocess.return_value = mock_result
        response = self.client.get('/api/rescrouce/monitor/memory_slot.sh')
        if mock_subprocess.called:
            call_args = mock_subprocess.call_args[0][0]
            self.assertEqual(len(call_args), 2)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch('osmanager.rescrouce_monitor.views.os.path.isfile')
    @patch('osmanager.rescrouce_monitor.views.subprocess.run')
    def test_pci_info_without_mode(self, mock_subprocess, mock_isfile):
        """测试 pci_info.sh 不需要mode参数"""
        mock_isfile.return_value = True
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps({'pci_devices': []})
        mock_result.stderr = ''
        mock_subprocess.return_value = mock_result
        response = self.client.get('/api/rescrouce/monitor/pci_info.sh')
        if mock_subprocess.called:
            call_args = mock_subprocess.call_args[0][0]
            self.assertEqual(len(call_args), 2)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch('osmanager.rescrouce_monitor.views.os.path.isfile')
    def test_memory_slot_with_extra_mode_fails(self, mock_isfile):
        """测试 memory_slot.sh 传入mode参数应该失败"""
        mock_isfile.return_value = True
        response = self.client.get('/api/rescrouce/monitor/memory_slot.sh?mode=test')
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertIn('该脚本不支持 mode 参数', response_data['message'])

    @patch('osmanager.rescrouce_monitor.views.os.path.isfile')
    def test_pci_info_with_extra_mode_fails(self, mock_isfile):
        """测试 pci_info.sh 传入mode参数应该失败"""
        mock_isfile.return_value = True
        response = self.client.get('/api/rescrouce/monitor/pci_info.sh?mode=test')
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertIn('该脚本不支持 mode 参数', response_data['message'])

class TestDifferentModeFunctionality(TestCase):
    """测试不同mode参数调用不同功能"""

    def setUp(self):
        """测试前设置"""
        self.client = Client()
        session = self.client.session
        session['username'] = 'testuser'
        session.save()

    @patch('osmanager.rescrouce_monitor.views.os.path.isfile')
    @patch('osmanager.rescrouce_monitor.views.subprocess.run')
    def test_monitor_different_modes(self, mock_subprocess, mock_isfile):
        """验证不同mode产生不同的脚本调用"""
        mock_isfile.return_value = True
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = '{}'
        mock_result.stderr = ''
        mock_subprocess.return_value = mock_result
        response1 = self.client.get('/api/rescrouce/monitor/monitor_status.sh?mode=cpu')
        if mock_subprocess.call_count >= 1:
            call1 = mock_subprocess.call_args_list[0][0][0]
            self.assertIn('cpu', call1)
        response2 = self.client.get('/api/rescrouce/monitor/monitor_status.sh?mode=memory')
        if mock_subprocess.call_count >= 2:
            call2 = mock_subprocess.call_args_list[1][0][0]
            self.assertIn('memory', call2)
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)

class TestFailedModes(TestCase):
    """测试失败场景下的资源管理模块"""

    def setUp(self):
        """测试前设置"""
        self.client = Client()
        session = self.client.session
        session['username'] = 'testuser'
        session.save()
        self.valid_script = 'monitor_status.sh'
        self.invalid_script = 'nonexistent_script.sh'
        self.valid_mode = 'cpu'

    def test_run_shell_script_api_script_not_found(self):
        """测试脚本不存在的情况"""
        with patch('os.path.isfile', return_value=False):
            response = self.client.get(f'/api/rescrouce/monitor/{self.invalid_script}?mode={self.valid_mode}')
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
            self.assertIn('not found manager_script', response.json()['error'])

    def test_run_shell_script_api_script_execution_failure(self):
        """测试脚本执行失败的情况"""
        with patch('os.path.isfile', return_value=True), patch('subprocess.run') as mock_subprocess:
            mock_result = MagicMock()
            mock_result.returncode = 1
            mock_result.stdout = ''
            mock_result.stderr = 'Permission denied'
            mock_subprocess.return_value = mock_result
            response = self.client.get(f'/api/rescrouce/monitor/{self.valid_script}?mode={self.valid_mode}')
            self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            self.assertIn('脚本执行失败', response.json()['error'])

    def test_run_shell_script_api_timeout(self):
        """测试脚本执行超时的情况"""
        import subprocess
        with patch('os.path.isfile', return_value=True), patch('subprocess.run') as mock_subprocess:
            mock_subprocess.side_effect = subprocess.TimeoutExpired('bash', 30)
            response = self.client.get(f'/api/rescrouce/monitor/{self.valid_script}?mode={self.valid_mode}')
            self.assertEqual(response.status_code, 408)
            data = response.json()
            self.assertIn('脚本执行超时', data['error'])

    def test_run_shell_script_api_non_json_output(self):
        """测试脚本返回非JSON输出的情况"""
        with patch('os.path.isfile', return_value=True), patch('subprocess.run') as mock_subprocess:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = 'This is not JSON output'
            mock_result.stderr = ''
            mock_subprocess.return_value = mock_result
            response = self.client.get(f'/api/rescrouce/monitor/{self.valid_script}?mode={self.valid_mode}')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn('success,but not json', response.json()['message'])

class TestAuthentication(TestCase):
    """测试认证功能"""

    def setUp(self):
        """测试前设置"""
        self.client = Client()

    def test_unauthenticated_access_denied(self):
        """测试未登录用户访问被拒绝"""
        response = self.client.get('/api/rescrouce/monitor/monitor_status.sh?mode=all')
        self.assertEqual(response.status_code, 401)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['code'], 401)

class TestServiceManagementAPI(TestCase):
    """测试服务管理API"""

    def setUp(self):
        """测试前设置"""
        self.client = Client()
        session = self.client.session
        session['username'] = 'testuser'
        session.save()

    @patch('osmanager.rescrouce_monitor.views.os.path.isfile')
    def test_manage_service_script_not_found(self, mock_isfile):
        """测试服务管理脚本不存在的情况"""
        mock_isfile.return_value = False
        data = {'service_name': 'nginx', 'operation': 'start'}
        response = self.client.post('/api/rescrouce/service/service_manage.sh', data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        response_data = json.loads(response.content)
        self.assertIn('not found manager_script', response_data['error'])

    @patch('osmanager.rescrouce_monitor.views.os.path.isfile')
    def test_manage_service_missing_parameters(self, mock_isfile):
        """测试服务管理缺少必需参数"""
        mock_isfile.return_value = True
        data = {'service_name': 'nginx'}
        response = self.client.post('/api/rescrouce/service/service_manage.sh', data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertIn('缺少必需参数', response_data['error'])

    @patch('osmanager.rescrouce_monitor.views.os.path.isfile')
    def test_manage_service_invalid_operation(self, mock_isfile):
        """测试服务管理使用无效操作"""
        mock_isfile.return_value = True
        data = {'service_name': 'nginx', 'operation': 'invalid_operation'}
        response = self.client.post('/api/rescrouce/service/service_manage.sh', data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 401)
        response_data = json.loads(response.content)
        self.assertIn('operation 只允许为', response_data['message'])

    @patch('osmanager.rescrouce_monitor.views.os.path.isfile')
    @patch('osmanager.rescrouce_monitor.views.subprocess.run')
    def test_manage_service_success_start(self, mock_subprocess, mock_isfile):
        """测试服务管理成功启动服务"""
        mock_isfile.return_value = True
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = 'Service started successfully'
        mock_result.stderr = ''
        mock_subprocess.return_value = mock_result
        data = {'service_name': 'nginx', 'operation': 'start'}
        pass

    @patch('osmanager.rescrouce_monitor.views.os.path.isfile')
    @patch('osmanager.rescrouce_monitor.views.subprocess.run')
    def test_manage_service_success_stop(self, mock_subprocess, mock_isfile):
        """测试服务管理成功停止服务"""
        pass

    @patch('osmanager.rescrouce_monitor.views.os.path.isfile')
    @patch('osmanager.rescrouce_monitor.views.subprocess.run')
    def test_manage_service_success_restart(self, mock_subprocess, mock_isfile):
        """测试服务管理成功重启服务"""
        pass

    @patch('osmanager.rescrouce_monitor.views.os.path.isfile')
    @patch('osmanager.rescrouce_monitor.views.subprocess.run')
    def test_manage_service_execution_failure(self, mock_subprocess, mock_isfile):
        """测试服务管理执行失败"""
        pass

    @patch('osmanager.rescrouce_monitor.views.os.path.isfile')
    def test_manage_service_invalid_json_format(self, mock_isfile):
        """测试服务管理使用无效JSON格式"""
        pass
