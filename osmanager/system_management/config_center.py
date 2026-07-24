import grp
import ipaddress
import pwd
import re
from pathlib import Path

try:
    import spwd
except ImportError:
    spwd = None

from .command import run_safe
from .snapshots import create_snapshot, register_snapshot_target, rollback_snapshot, write_registered_text


CHRONY_PATH = Path('/etc/chrony.conf')
CHRONY_TARGET = 'chrony-config'
SELINUX_CONFIG_PATH = Path('/etc/selinux/config')
ACCOUNT_NAME_PATTERN = re.compile(r'^[a-z_][a-z0-9_-]{0,30}\$?$')
HOST_LABEL_PATTERN = re.compile(r'^[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?$')


class SystemOperationError(RuntimeError):
    pass


class OperationConflict(RuntimeError):
    pass


def _run(args, allowed, timeout=15):
    result = run_safe(args, allowed, timeout=timeout)
    if not result.success:
        raise SystemOperationError(result.stderr.strip() or result.stdout.strip() or '系统命令执行失败')
    return result


def _valid_host(value):
    try:
        ipaddress.ip_address(value)
        return True
    except ValueError:
        labels = value.rstrip('.').split('.')
        return bool(labels) and len(value) <= 253 and all(HOST_LABEL_PATTERN.fullmatch(label) for label in labels)


def normalize_ntp_sources(sources):
    if not isinstance(sources, list) or not 1 <= len(sources) <= 8:
        raise ValueError('NTP 源数量必须为 1 到 8')
    normalized = []
    seen = set()
    for item in sources:
        if not isinstance(item, dict):
            raise ValueError('NTP 源格式不合法')
        mode = str(item.get('mode', 'server')).strip().lower()
        address = str(item.get('address', '')).strip()
        if mode not in ('server', 'pool') or not _valid_host(address):
            raise ValueError('NTP 源类型或地址不合法')
        key = (mode, address.lower())
        if key in seen:
            continue
        seen.add(key)
        normalized.append({'mode': mode, 'address': address, 'iburst': bool(item.get('iburst', True))})
    if not normalized:
        raise ValueError('至少需要一个有效 NTP 源')
    return normalized


def parse_chrony_sources(content):
    sources = []
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue
        parts = stripped.split()
        if len(parts) >= 2 and parts[0] in ('server', 'pool'):
            sources.append({'mode': parts[0], 'address': parts[1], 'iburst': 'iburst' in parts[2:]})
    return sources


def replace_chrony_sources(content, sources):
    normalized = normalize_ntp_sources(sources)
    lines = content.splitlines()
    source_indexes = []
    kept_lines = []
    for index, line in enumerate(lines):
        parts = line.strip().split()
        if parts and not line.lstrip().startswith('#') and parts[0] in ('server', 'pool'):
            source_indexes.append(index)
            continue
        kept_lines.append(line)
    insert_at = source_indexes[0] if source_indexes else 0
    insert_at = min(insert_at, len(kept_lines))
    rendered = [f"{item['mode']} {item['address']}{' iburst' if item['iburst'] else ''}" for item in normalized]
    updated = kept_lines[:insert_at] + rendered + kept_lines[insert_at:]
    return '\n'.join(updated).rstrip() + '\n'


def validate_chrony_content(content):
    if '\x00' in content or not parse_chrony_sources(content):
        raise ValueError('chrony 配置必须包含至少一个有效 server 或 pool')


def chronyd_state():
    result = run_safe(['systemctl', 'is-active', 'chronyd'], {'systemctl'}, timeout=3)
    return result.stdout.strip() or 'inactive'


def apply_chrony_config():
    if chronyd_state() == 'active':
        _run(['systemctl', 'restart', 'chronyd'], {'systemctl'}, timeout=30)


register_snapshot_target(CHRONY_TARGET, CHRONY_PATH, validate_chrony_content, apply_chrony_config)


def _chrony_tracking():
    result = run_safe(['chronyc', 'tracking', '-n'], {'chronyc'}, timeout=5)
    values = {}
    if result.success:
        for line in result.stdout.splitlines():
            if ':' in line:
                key, value = line.split(':', 1)
                values[key.strip().lower().replace(' ', '_')] = value.strip()
    return values


def get_ntp_status():
    content = CHRONY_PATH.read_text(encoding='utf-8')
    enabled = run_safe(['systemctl', 'is-enabled', 'chronyd'], {'systemctl'}, timeout=3)
    return {
        'service_state': chronyd_state(),
        'enabled': enabled.stdout.strip() == 'enabled',
        'sources': parse_chrony_sources(content),
        'tracking': _chrony_tracking(),
    }


def update_ntp(payload, actor):
    if not isinstance(payload, dict):
        raise ValueError('请求体必须为对象')
    enabled = payload.get('enabled')
    if not isinstance(enabled, bool):
        raise ValueError('enabled 必须为布尔值')
    sources = normalize_ntp_sources(payload.get('sources'))
    current = CHRONY_PATH.read_text(encoding='utf-8')
    updated = replace_chrony_sources(current, sources)
    snapshot = create_snapshot(actor, 'config_center', CHRONY_TARGET, '更新 NTP 配置前快照')
    try:
        if updated != current:
            write_registered_text(CHRONY_TARGET, updated)
        command = ['systemctl', 'enable' if enabled else 'disable', '--now', 'chronyd']
        _run(command, {'systemctl'}, timeout=30)
    except Exception:
        rollback_snapshot(snapshot, actor, 'NTP 更新失败安全恢复')
        raise
    return get_ntp_status(), snapshot


def _locked(username):
    if not spwd:
        return None
    try:
        password = spwd.getspnam(username).sp_pwdp
    except (KeyError, PermissionError):
        return None
    return password.startswith(('!', '*'))


def available_shells():
    path = Path('/etc/shells')
    if not path.exists():
        return ['/bin/bash', '/bin/sh']
    return [line.strip() for line in path.read_text(encoding='utf-8').splitlines()
            if line.strip().startswith('/') and not line.lstrip().startswith('#')]


def list_accounts():
    groups = grp.getgrall()
    group_by_gid = {item.gr_gid: item.gr_name for item in groups}
    supplementary = {}
    for item in groups:
        for member in item.gr_mem:
            supplementary.setdefault(member, []).append(item.gr_name)
    users = []
    for item in pwd.getpwall():
        user_groups = sorted(set([group_by_gid.get(item.pw_gid, str(item.pw_gid)), *supplementary.get(item.pw_name, [])]))
        users.append({
            'username': item.pw_name,
            'uid': item.pw_uid,
            'gid': item.pw_gid,
            'home': item.pw_dir,
            'shell': item.pw_shell,
            'gecos': item.pw_gecos,
            'locked': _locked(item.pw_name),
            'system': item.pw_uid < 1000 and item.pw_uid != 0,
            'groups': user_groups,
        })
    group_items = [
        {'name': item.gr_name, 'gid': item.gr_gid, 'members': sorted(item.gr_mem), 'system': item.gr_gid < 1000}
        for item in groups
    ]
    return {'users': users, 'groups': group_items, 'shells': available_shells()}


def validate_account_name(name):
    value = str(name or '').strip()
    if not ACCOUNT_NAME_PATTERN.fullmatch(value):
        raise ValueError('用户或组名称格式不合法')
    return value


def _user(username):
    try:
        return pwd.getpwnam(validate_account_name(username))
    except KeyError as error:
        raise ValueError('用户不存在') from error


def _group(group_name):
    try:
        return grp.getgrnam(validate_account_name(group_name))
    except KeyError as error:
        raise ValueError('组不存在') from error


def create_group(name):
    name = validate_account_name(name)
    try:
        grp.getgrnam(name)
    except KeyError:
        _run(['groupadd', name], {'groupadd'})
        return grp.getgrnam(name)
    raise ValueError('组已存在')


def delete_group(name):
    group = _group(name)
    if group.gr_gid == 0:
        raise ValueError('禁止删除 GID 0 组')
    _run(['groupdel', group.gr_name], {'groupdel'})


def create_user(payload):
    if not isinstance(payload, dict):
        raise ValueError('请求体必须为对象')
    username = validate_account_name(payload.get('username'))
    try:
        pwd.getpwnam(username)
    except KeyError:
        pass
    else:
        raise ValueError('用户已存在')
    shell = str(payload.get('shell') or '/bin/bash')
    if shell not in available_shells():
        raise ValueError('shell 不在允许列表')
    args = ['useradd', '--create-home', '--shell', shell]
    primary_group = payload.get('primary_group')
    if primary_group:
        args.extend(['--gid', _group(primary_group).gr_name])
    args.append(username)
    _run(args, {'useradd'}, timeout=30)
    _run(['usermod', '--lock', username], {'usermod'})
    return pwd.getpwnam(username)


def update_user(username, payload):
    user = _user(username)
    if user.pw_uid == 0:
        raise ValueError('禁止修改 UID 0 用户')
    if not isinstance(payload, dict):
        raise ValueError('请求体必须为对象')
    if 'shell' in payload:
        shell = str(payload['shell'])
        if shell not in available_shells():
            raise ValueError('shell 不在允许列表')
        _run(['usermod', '--shell', shell, user.pw_name], {'usermod'})
    if 'locked' in payload:
        if not isinstance(payload['locked'], bool):
            raise ValueError('locked 必须为布尔值')
        _run(['usermod', '--lock' if payload['locked'] else '--unlock', user.pw_name], {'usermod'})
    add_groups = payload.get('add_groups', [])
    if not isinstance(add_groups, list):
        raise ValueError('add_groups 必须为数组')
    for group_name in add_groups:
        group = _group(group_name)
        _run(['gpasswd', '--add', user.pw_name, group.gr_name], {'gpasswd'})


def delete_user(username, remove_home=False):
    user = _user(username)
    if user.pw_uid == 0:
        raise ValueError('禁止删除 UID 0 用户')
    args = ['userdel']
    if remove_home:
        args.append('--remove')
    args.append(user.pw_name)
    _run(args, {'userdel'}, timeout=30)


def get_selinux_status():
    runtime = run_safe(['getenforce'], {'getenforce'}, timeout=3)
    configured = {}
    if SELINUX_CONFIG_PATH.exists():
        for line in SELINUX_CONFIG_PATH.read_text(encoding='utf-8').splitlines():
            if '=' in line and not line.lstrip().startswith('#'):
                key, value = line.split('=', 1)
                if key in ('SELINUX', 'SELINUXTYPE'):
                    configured[key.lower()] = value.strip()
    return {'runtime': runtime.stdout.strip() or 'Unavailable', 'configured': configured}


def set_selinux_mode(mode):
    normalized = str(mode or '').strip().lower()
    if normalized not in ('enforcing', 'permissive'):
        raise ValueError('SELinux 模式只允许 enforcing 或 permissive')
    status = get_selinux_status()
    if status['runtime'] == 'Disabled':
        raise OperationConflict('SELinux 当前为 Disabled，无法运行时切换')
    _run(['setenforce', '1' if normalized == 'enforcing' else '0'], {'setenforce'})
    return get_selinux_status()