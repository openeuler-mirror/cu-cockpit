"""
Service 模块测试用例
测试服务状态查询和服务管理功能
import pytest
import json
from unittest.mock import patch, MagicMock
from django.test import Client
from rest_framework import status
"""
import os
import sys
import django
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'osmanager.settings')
django.setup()
import pytest
import json
from unittest.mock import patch, MagicMock
from django.test import Client
from rest_framework import status

class TestGetServiceStatusApi:
    """测试获取服务状态接口"""

    @patch('osmanager.service.views.os.path.isfile')
    @patch('osmanager.service.views.subprocess.run')
    def test_get_service_status_success(self, mock_subprocess, mock_isfile):
        """测试成功获取服务状态"""
        mock_isfile.return_value = True
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps([{'服务名称': 'nginx', '运行状态': 'active', '注册状态': 'enabled', '描述': 'nginx web server'}, {'服务名称': 'mysql', '运行状态': 'inactive', '注册状态': 'enabled', '描述': 'mysql database server'}])
        mock_result.stderr = ''
        mock_subprocess.return_value = mock_result
        client = Client()
        session = client.session
        session['username'] = 'testuser'
        session.save()
        response = client.get('/api/service/status')
        assert response.status_code == status.HTTP_200_OK
        response_data = json.loads(response.content)
        assert isinstance(response_data, list)
        assert len(response_data) == 2
        assert response_data[0]['服务名称'] == 'nginx'

    @patch('osmanager.service.views.os.path.isfile')
    def test_get_service_status_script_not_found(self, mock_isfile):
        """测试脚本文件不存在"""
        mock_isfile.return_value = False
        client = Client()
        session = client.session
        session['username'] = 'testuser'
        session.save()
        response = client.get('/api/service/status')
        assert response.status_code == 404
        response_data = json.loads(response.content)
        assert 'not found manager_script' in response_data['error']

    @patch('osmanager.service.views.os.path.isfile')
    @patch('osmanager.service.views.subprocess.run')
    def test_get_service_status_execution_failure(self, mock_subprocess, mock_isfile):
        """测试脚本执行失败"""
        mock_isfile.return_value = True
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ''
        mock_result.stderr = 'Command failed'
        mock_subprocess.return_value = mock_result
        client = Client()
        session = client.session
        session['username'] = 'testuser'
        session.save()
        response = client.get('/api/service/status')
        assert response.status_code == 500
        response_data = json.loads(response.content)
        assert '获取服务状态失败' in response_data['error']

class TestManageServiceApi:
    """测试服务管理接口"""

    @patch('osmanager.service.views.os.path.isfile')
    @patch('osmanager.service.views.subprocess.run')
    def test_start_service_success(self, mock_subprocess, mock_isfile):
        """测试启动服务成功"""
        mock_isfile.return_value = True
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = 'Service started successfully'
        mock_result.stderr = ''
        mock_subprocess.return_value = mock_result
        client = Client()
        session = client.session
        session['username'] = 'testuser'
        session.save()
        data = {'service_name': 'nginx', 'operation': 'start'}
        response = client.post('/api/service/manage', data=json.dumps(data), content_type='application/json')
        assert response.status_code == status.HTTP_200_OK
        response_data = json.loads(response.content)
        assert response_data['success_flag'] is True
        assert 'nginx' in response_data['message']
        assert 'start' in response_data['message']

    @patch('osmanager.service.views.os.path.isfile')
    @patch('osmanager.service.views.subprocess.run')
    def test_stop_service_success(self, mock_subprocess, mock_isfile):
        """测试停止服务成功"""
        mock_isfile.return_value = True
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = 'Service stopped successfully'
        mock_result.stderr = ''
        mock_subprocess.return_value = mock_result
        client = Client()
        session = client.session
        session['username'] = 'testuser'
        session.save()
        data = {'service_name': 'nginx', 'operation': 'stop'}
        response = client.post('/api/service/manage', data=json.dumps(data), content_type='application/json')
        assert response.status_code == status.HTTP_200_OK
        response_data = json.loads(response.content)
        assert response_data['success_flag'] is True

    @patch('osmanager.service.views.os.path.isfile')
    @patch('osmanager.service.views.subprocess.run')
    def test_restart_service_success(self, mock_subprocess, mock_isfile):
        """测试重启服务成功"""
        mock_isfile.return_value = True
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = 'Service restarted successfully'
        mock_result.stderr = ''
        mock_subprocess.return_value = mock_result
        client = Client()
        session = client.session
        session['username'] = 'testuser'
        session.save()
        data = {'service_name': 'nginx', 'operation': 'restart'}
        response = client.post('/api/service/manage', data=json.dumps(data), content_type='application/json')
        assert response.status_code == status.HTTP_200_OK
        response_data = json.loads(response.content)
        assert response_data['success_flag'] is True

    def test_manage_service_missing_parameters(self):
        """测试缺少必需参数"""
        client = Client()
        session = client.session
        session['username'] = 'testuser'
        session.save()
        data = {'service_name': 'nginx'}
        response = client.post('/api/service/manage', data=json.dumps(data), content_type='application/json')
        assert response.status_code == 400
        response_data = json.loads(response.content)
        assert '缺少必需参数' in response_data['error']

    def test_manage_service_invalid_operation(self):
        """测试无效的操作类型"""
        client = Client()
        session = client.session
        session['username'] = 'testuser'
        session.save()
        data = {'service_name': 'nginx', 'operation': 'invalid_op'}
        response = client.post('/api/service/manage', data=json.dumps(data), content_type='application/json')
        assert response.status_code == 401
        response_data = json.loads(response.content)
        assert 'operation 只允许为' in response_data['message']

    @patch('osmanager.service.views.os.path.isfile')
    @patch('osmanager.service.views.subprocess.run')
    def test_manage_service_execution_failure(self, mock_subprocess, mock_isfile):
        """测试服务管理执行失败"""
        mock_isfile.return_value = True
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = 'Service not found'
        mock_result.stderr = 'Failed to start service'
        mock_subprocess.return_value = mock_result
        client = Client()
        session = client.session
        session['username'] = 'testuser'
        session.save()
        data = {'service_name': 'nonexistent', 'operation': 'start'}
        response = client.post('/api/service/manage', data=json.dumps(data), content_type='application/json')
        assert response.status_code == 402
        response_data = json.loads(response.content)
        assert response_data['success_flag'] is False
        assert '操作失败' in response_data['message']

class TestServiceAuthentication:
    """测试服务模块认证功能"""

    def test_unauthenticated_access_denied(self):
        """测试未登录用户访问被拒绝"""
        client = Client()
        response = client.get('/api/service/status')
        assert response.status_code == 401
        response_data = json.loads(response.content)
        assert response_data['code'] == 401
