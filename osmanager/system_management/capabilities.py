import os
import shutil
import socket

from django.utils import timezone

from .command import SAFE_PATH, UnsafeCommandError, run_safe


COMMANDS = (
    'chronyd', 'chronyc', 'crontab', 'firewall-cmd', 'getenforce', 'groupadd',
    'groupdel', 'gpasswd', 'ip', 'kill', 'ps', 'semanage', 'setenforce', 'ss', 'systemctl',
    'timedatectl', 'useradd', 'userdel', 'usermod',
)
SERVICES = ('crond', 'chronyd', 'firewalld', 'systemd-timesyncd')
WEBSSH_PORT = int(os.environ.get('WEBSSH_PORT', '8002'))


def command_exists(name):
    return shutil.which(name, path=SAFE_PATH) is not None


def service_state(name):
    if not command_exists('systemctl'):
        return 'unknown'
    try:
        result = run_safe(['systemctl', 'is-active', name], {'systemctl'}, timeout=3)
    except (UnsafeCommandError, OSError):
        return 'unknown'
    value = result.stdout.strip()
    return value or ('inactive' if result.returncode else 'active')


def selinux_state():
    if not command_exists('getenforce'):
        return 'Unavailable'
    try:
        result = run_safe(['getenforce'], {'getenforce'}, timeout=3)
    except (UnsafeCommandError, OSError):
        return 'Unavailable'
    return result.stdout.strip() or 'Unknown'


def terminal_proxy_available():
    try:
        with socket.create_connection(('127.0.0.1', WEBSSH_PORT), timeout=0.3):
            return True
    except OSError:
        return False


def detect_capabilities():
    commands = {name: command_exists(name) for name in COMMANDS}
    services = {name: service_state(name) for name in SERVICES}
    selinux = selinux_state()
    firewall_ready = commands['firewall-cmd'] and services['firewalld'] == 'active'
    cron_ready = commands['crontab'] and services['crond'] == 'active'
    config_ready = commands['timedatectl'] and commands['chronyc'] and services['chronyd'] == 'active'
    return {
        'checked_at': timezone.now().isoformat(),
        'commands': commands,
        'services': services,
        'selinux': {'state': selinux, 'runtime_switch': selinux in ('Enforcing', 'Permissive')},
        'modules': {
            'foundation': {'available': True, 'read_only': False, 'reason': ''},
            'config_center': {
                'available': commands['timedatectl'],
                'read_only': not config_ready,
                'reason': '' if config_ready else 'chronyd 未运行或管理命令不可用',
            },
            'cron': {
                'available': commands['crontab'],
                'read_only': not cron_ready,
                'reason': '' if cron_ready else 'crond 未运行或 crontab 不可用',
            },
            'process': {'available': os.path.isdir('/proc'), 'read_only': False, 'reason': ''},
            'network': {
                'available': commands['ip'] and commands['ss'],
                'read_only': False,
                'reason': '' if commands['ip'] and commands['ss'] else 'ip 或 ss 命令不可用',
            },
            'firewall': {
                'available': commands['firewall-cmd'],
                'read_only': not firewall_ready,
                'reason': '' if firewall_ready else 'firewalld 服务未运行',
            },
            'terminal': {
                'available': terminal_proxy_available(),
                'read_only': False,
                'reason': '' if terminal_proxy_available() else f'WebSSH 代理未监听 {WEBSSH_PORT} 端口',
            },
        },
    }