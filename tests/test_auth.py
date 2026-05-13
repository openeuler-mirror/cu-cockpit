"""
auth 模块单元测试
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

class AuthViewsTest(TestCase):

    def setUp(self):
        """测试初始化设置"""
        self.client = APIClient()
        self.valid_username = 'testuser'
        self.valid_password = 'testpass123'
        self.invalid_username = 'invaliduser'
        self.invalid_password = 'wrongpass'
        self.empty_username = ''
        self.empty_password = ''

    def test_login_view_success(self):
        """测试成功登录的情况"""
        with patch('osmanager.auth.views.verify_with_pam', return_value=True):
            data = {'username': self.valid_username, 'password': self.valid_password}
            response = self.client.post('/api/auth/login/', data, format='json')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            response_data = response.json()
            self.assertEqual(response_data['code'], 200)
            self.assertEqual(response_data['message'], '登录成功')
            self.assertEqual(response_data['user'], self.valid_username)

    def test_login_view_json_format(self):
        """测试JSON格式的登录请求"""
        with patch('osmanager.auth.views.verify_with_pam', return_value=True):
            data = {'username': self.valid_username, 'password': self.valid_password}
            response = self.client.post('/api/auth/login/', data, format='json')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            response_data = response.json()
            self.assertEqual(response_data['code'], 200)
            self.assertEqual(response_data['user'], self.valid_username)

    def test_login_view_form_format(self):
        """测试表单格式的登录请求"""
        with patch('osmanager.auth.views.verify_with_pam', return_value=True):
            data = {'username': self.valid_username, 'password': self.valid_password}
            response = self.client.post('/api/auth/login/', data)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            response_data = response.json()
            self.assertEqual(response_data['code'], 200)
            self.assertEqual(response_data['user'], self.valid_username)

    def test_login_view_missing_username(self):
        """测试缺少用户名的情况"""
        data = {'password': self.valid_password}
        response = self.client.post('/api/auth/login/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = response.json()
        self.assertEqual(response_data['code'], 400)
        self.assertEqual(response_data['message'], '请输入用户名和密码')

    def test_login_view_missing_password(self):
        """测试缺少密码的情况"""
        data = {'username': self.valid_username}
        response = self.client.post('/api/auth/login/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = response.json()
        self.assertEqual(response_data['code'], 400)
        self.assertEqual(response_data['message'], '请输入用户名和密码')

    def test_login_view_empty_username(self):
        """测试空用户名的情况"""
        data = {'username': self.empty_username, 'password': self.valid_password}
        response = self.client.post('/api/auth/login/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = response.json()
        self.assertEqual(response_data['code'], 400)
        self.assertEqual(response_data['message'], '请输入用户名和密码')

    def test_login_view_empty_password(self):
        """测试空密码的情况"""
        data = {'username': self.valid_username, 'password': self.empty_password}
        response = self.client.post('/api/auth/login/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = response.json()
        self.assertEqual(response_data['code'], 400)
        self.assertEqual(response_data['message'], '请输入用户名和密码')

    def test_login_view_empty_credentials(self):
        """测试用户名和密码都为空的情况"""
        data = {'username': self.empty_username, 'password': self.empty_password}
        response = self.client.post('/api/auth/login/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = response.json()
        self.assertEqual(response_data['code'], 400)
        self.assertEqual(response_data['message'], '请输入用户名和密码')

    def test_login_view_invalid_credentials(self):
        """测试无效凭据的情况"""
        with patch('osmanager.auth.views.verify_with_pam', return_value=False):
            data = {'username': self.invalid_username, 'password': self.invalid_password}
            response = self.client.post('/api/auth/login/', data, format='json')
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
            response_data = response.json()
            self.assertEqual(response_data['code'], 401)
            self.assertEqual(response_data['message'], '用户名或密码错误')

    def test_login_view_pam_not_available(self):
        """测试PAM服务不可用的情况"""
        from osmanager.auth.auth_pam import PamNotAvailable
        with patch('osmanager.auth.views.verify_with_pam', side_effect=PamNotAvailable('python-pam 未安装')):
            data = {'username': self.valid_username, 'password': self.valid_password}
            response = self.client.post('/api/auth/login/', data, format='json')
            self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            response_data = response.json()
            self.assertEqual(response_data['code'], 500)
            self.assertEqual(response_data['message'], '认证服务不可用，请安装系统包python3-pam')

    def test_login_view_pam_auth_error(self):
        """测试PAM认证异常的情况"""
        from osmanager.auth.auth_pam import PamAuthError
        with patch('osmanager.auth.views.verify_with_pam', side_effect=PamAuthError('PAM 认证异常')):
            data = {'username': self.valid_username, 'password': self.valid_password}
            response = self.client.post('/api/auth/login/', data, format='json')
            self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            response_data = response.json()
            self.assertEqual(response_data['code'], 500)
            self.assertEqual(response_data['message'], 'PAM 认证异常')

    def test_login_view_get_method(self):
        """测试使用GET方法请求登录的情况"""
        response = self.client.get('/api/auth/login/')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_login_view_session_storage(self):
        """测试登录成功后session存储的情况"""
        with patch('osmanager.auth.views.verify_with_pam', return_value=True):
            data = {'username': self.valid_username, 'password': self.valid_password}
            response = self.client.post('/api/auth/login/', data, format='json')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(self.client.session.get('username'), self.valid_username)

    def test_logout_view_success(self):
        """测试成功登出的情况"""
        session = self.client.session
        session['username'] = self.valid_username
        session.save()
        response = self.client.post('/api/auth/logout/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        self.assertEqual(response_data['code'], 200)
        self.assertEqual(response_data['message'], '登出成功')

    def test_logout_view_no_session(self):
        """测试没有session时的登出情况"""
        response = self.client.post('/api/auth/logout/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        self.assertEqual(response_data['code'], 200)
        self.assertEqual(response_data['message'], '登出成功')

    def test_logout_view_session_cleared(self):
        """测试登出后session被清除的情况"""
        pass

    def test_logout_view_exception(self):
        """测试登出过程中发生异常的情况"""
        pass

    def test_logout_view_get_method(self):
        """测试使用GET方法请求登出的情况"""
        pass

    def test_login_logout_flow(self):
        """测试完整的登录-登出流程"""
        pass

    def test_multiple_login_attempts(self):
        """测试多次登录尝试的情况"""
        pass

    def test_login_with_special_characters(self):
        """测试用户名包含特殊字符的情况"""
        pass

    def test_login_with_long_password(self):
        """测试长密码的情况"""
        pass

    def test_login_with_unicode_username(self):
        """测试Unicode用户名的情况"""
        pass
