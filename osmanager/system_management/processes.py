import os
import re
import signal
from pathlib import Path

from .command import run_safe


PS_ARGS = ['ps', '-eo', 'pid=,ppid=,user=,stat=,pcpu=,pmem=,etimes=,comm=,args=', '--no-headers']
SORT_FIELDS = {
    'pid': 'pid',
    'user': 'user',
    'cpu': 'cpu',
    'memory': 'memory',
    'elapsed': 'elapsed_seconds',
    'name': 'name',
}
STATUS_LABELS = {
    'R': 'running',
    'S': 'sleeping',
    'D': 'uninterruptible',
    'T': 'stopped',
    't': 'tracing',
    'Z': 'zombie',
    'X': 'dead',
    'I': 'idle',
}
SENSITIVE_COMMAND_PATTERN = re.compile(
    r'(?i)((?:--?|/)(?:password|passwd|token|secret|api[-_]?key)(?:=|\s+))(\S+)'
)
URI_CREDENTIAL_PATTERN = re.compile(r'(?i)([a-z][a-z0-9+.-]*://[^\s:/@]+:)([^\s@]+)(@)')


def redact_command(command):
    value = SENSITIVE_COMMAND_PATTERN.sub(r'\1[REDACTED]', str(command or ''))
    return URI_CREDENTIAL_PATTERN.sub(r'\1[REDACTED]\3', value)


class ProcessNotFound(ValueError):
    pass


def _platform_pids():
    protected = {1, os.getpid(), os.getppid()}
    current = os.getppid()
    for _ in range(8):
        stat_path = Path(f'/proc/{current}/stat')
        try:
            parts = stat_path.read_text(encoding='utf-8').split()
            parent = int(parts[3])
        except (OSError, ValueError, IndexError):
            break
        if parent <= 0 or parent in protected:
            break
        protected.add(parent)
        current = parent
    return protected


def _protected_reason(item, platform_pids):
    if item['pid'] <= 1:
        return '系统初始化进程受保护'
    if item['pid'] in platform_pids:
        return '平台当前进程或父进程受保护'
    command = item['command'].lower()
    if 'gunicorn' in command and 'osmanager.wsgi' in command:
        return 'cu-cockpit 后端进程受保护'
    return ''


def parse_ps_output(output):
    platform_pids = _platform_pids()
    items = []
    for line in output.splitlines():
        fields = line.strip().split(None, 8)
        if len(fields) < 8:
            continue
        if len(fields) == 8:
            fields.append(fields[7])
        try:
            pid, ppid = int(fields[0]), int(fields[1])
            cpu, memory = float(fields[4]), float(fields[5])
            elapsed = int(fields[6])
        except ValueError:
            continue
        item = {
            'pid': pid,
            'ppid': ppid,
            'user': fields[2],
            'stat': fields[3],
            'status': STATUS_LABELS.get(fields[3][:1], 'unknown'),
            'cpu': cpu,
            'memory': memory,
            'elapsed_seconds': elapsed,
            'name': fields[7],
            'command': redact_command(fields[8]),
        }
        reason = _protected_reason(item, platform_pids)
        item['protected'] = bool(reason)
        item['protected_reason'] = reason
        items.append(item)
    return items


def list_processes(search='', sort='cpu', order='desc', limit=500):
    result = run_safe(PS_ARGS, {'ps'}, timeout=8)
    if not result.success:
        raise RuntimeError(result.stderr.strip() or '无法读取进程列表')
    items = parse_ps_output(result.stdout)
    keyword = str(search or '').strip().lower()
    if keyword:
        items = [item for item in items if keyword in str(item['pid']) or keyword in item['user'].lower()
                 or keyword in item['name'].lower() or keyword in item['command'].lower()]
    sort_key = SORT_FIELDS.get(sort, 'cpu')
    reverse = order != 'asc'
    items.sort(key=lambda item: item[sort_key], reverse=reverse)
    safe_limit = max(1, min(int(limit), 2000))
    summary = {
        'total': len(items),
        'running': sum(1 for item in items if item['status'] == 'running'),
        'sleeping': sum(1 for item in items if item['status'] in ('sleeping', 'idle')),
        'zombie': sum(1 for item in items if item['status'] == 'zombie'),
    }
    return {'items': items[:safe_limit], 'summary': summary, 'sort': sort_key, 'order': 'desc' if reverse else 'asc'}


def _status_file(pid):
    values = {}
    try:
        content = Path(f'/proc/{pid}/status').read_text(encoding='utf-8')
    except FileNotFoundError as error:
        raise ProcessNotFound('进程不存在或已经退出') from error
    for line in content.splitlines():
        if ':' in line:
            key, value = line.split(':', 1)
            values[key.strip()] = value.strip()
    return values


def get_process_detail(pid):
    try:
        process_id = int(pid)
    except (TypeError, ValueError) as error:
        raise ValueError('PID 必须为正整数') from error
    if process_id <= 0:
        raise ValueError('PID 必须为正整数')
    matches = [item for item in list_processes(sort='pid', order='asc', limit=2000)['items'] if item['pid'] == process_id]
    if not matches:
        raise ProcessNotFound('进程不存在或已经退出')
    item = matches[0]
    status = _status_file(process_id)
    try:
        command_line = redact_command(Path(f'/proc/{process_id}/cmdline').read_bytes().replace(b'\x00', b' ').decode('utf-8', errors='replace').strip())
    except OSError:
        command_line = item['command']
    try:
        cwd = os.readlink(f'/proc/{process_id}/cwd')
    except OSError:
        cwd = ''
    try:
        file_descriptors = len(list(Path(f'/proc/{process_id}/fd').iterdir()))
    except OSError:
        file_descriptors = None
    return {
        **item,
        'command_line': command_line,
        'cwd': cwd,
        'threads': int(status.get('Threads', '0') or 0),
        'vm_size': status.get('VmSize', ''),
        'vm_rss': status.get('VmRSS', ''),
        'context_switches': {
            'voluntary': status.get('voluntary_ctxt_switches', ''),
            'nonvoluntary': status.get('nonvoluntary_ctxt_switches', ''),
        },
        'file_descriptors': file_descriptors,
    }


def send_process_signal(pid, signal_name, confirm_pid):
    detail = get_process_detail(pid)
    try:
        confirmed = int(confirm_pid)
    except (TypeError, ValueError) as error:
        raise ValueError('confirm_pid 必须与目标 PID 一致') from error
    if confirmed != detail['pid']:
        raise ValueError('confirm_pid 必须与目标 PID 一致')
    normalized = str(signal_name or '').upper()
    signals = {'TERM': signal.SIGTERM, 'KILL': signal.SIGKILL}
    if normalized not in signals:
        raise ValueError('只允许 TERM 或 KILL 信号')
    if detail['protected']:
        raise ValueError(detail['protected_reason'])
    try:
        os.kill(detail['pid'], signals[normalized])
    except ProcessLookupError as error:
        raise ProcessNotFound('进程已经退出') from error
    except PermissionError as error:
        raise ValueError('没有权限向该进程发送信号') from error
    return detail, normalized