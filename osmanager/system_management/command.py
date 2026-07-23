import os
import shutil
import subprocess
import time
from dataclasses import asdict, dataclass


SAFE_PATH = '/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin'
MAX_TIMEOUT_SECONDS = 60
DEFAULT_OUTPUT_LIMIT = 1024 * 1024


class UnsafeCommandError(ValueError):
    pass


class CommandExecutionTimeout(TimeoutError):
    def __init__(self, command, timeout):
        super().__init__(f'命令执行超过 {timeout} 秒')
        self.command = command
        self.timeout = timeout

    def to_dict(self):
        return {'timed_out': True, 'timeout': self.timeout, 'command': self.command[0]}


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: str
    stderr: str
    duration_ms: int
    stdout_truncated: bool
    stderr_truncated: bool

    @property
    def success(self):
        return self.returncode == 0

    def to_dict(self):
        data = asdict(self)
        data['success'] = self.success
        return data


def _validate_args(args, allowed_commands):
    if not isinstance(args, (list, tuple)) or not args:
        raise UnsafeCommandError('命令 argv 不能为空')
    if not all(isinstance(item, str) for item in args):
        raise UnsafeCommandError('命令参数必须为字符串')
    if any('\x00' in item or '\n' in item or '\r' in item for item in args):
        raise UnsafeCommandError('命令参数包含禁止字符')
    executable = args[0]
    if '/' in executable or executable not in set(allowed_commands):
        raise UnsafeCommandError('命令不在允许列表')
    resolved = shutil.which(executable, path=SAFE_PATH)
    if not resolved:
        raise UnsafeCommandError('命令不存在')
    return [resolved, *args[1:]]


def _decode_limited(value, limit):
    truncated = len(value) > limit
    if truncated:
        value = value[:limit]
    return value.decode('utf-8', errors='replace'), truncated


def run_safe(args, allowed_commands, timeout=10, output_limit=DEFAULT_OUTPUT_LIMIT):
    command = _validate_args(args, allowed_commands)
    safe_timeout = max(0.1, min(float(timeout), MAX_TIMEOUT_SECONDS))
    safe_limit = max(1024, min(int(output_limit), DEFAULT_OUTPUT_LIMIT))
    started = time.monotonic()
    try:
        completed = subprocess.run(
            command,
            shell=False,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=safe_timeout,
            env={'PATH': SAFE_PATH, 'LANG': 'C.UTF-8', 'LC_ALL': 'C.UTF-8'},
            close_fds=True,
        )
    except subprocess.TimeoutExpired as error:
        raise CommandExecutionTimeout(command, safe_timeout) from error
    stdout, stdout_truncated = _decode_limited(completed.stdout, safe_limit)
    stderr, stderr_truncated = _decode_limited(completed.stderr, safe_limit)
    return CommandResult(
        returncode=completed.returncode,
        stdout=stdout,
        stderr=stderr,
        duration_ms=round((time.monotonic() - started) * 1000),
        stdout_truncated=stdout_truncated,
        stderr_truncated=stderr_truncated,
    )