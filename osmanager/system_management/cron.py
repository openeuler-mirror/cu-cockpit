import os
import shlex
import tempfile
from pathlib import Path

from django.db import transaction
from django.utils import timezone

from .command import CommandExecutionTimeout, CommandResult, run_safe
from .models import CronExecution, CronJob


CRON_FILE = Path('/etc/cron.d/cu-cockpit')
MANAGE_PY = '/opt/cu-cockpit/manage.py'
PYTHON = '/opt/cu-cockpit/venv/bin/python'
ALLOWED_CRON_COMMANDS = {'date', 'df', 'echo', 'free', 'logger', 'true', 'uptime'}
FORBIDDEN_TOKENS = {'|', '||', '&&', ';', '>', '>>', '<', '<<'}
SCHEDULE_CHARS = set('0123456789*,-/')


def validate_schedule(schedule):
    value = str(schedule or '').strip()
    fields = value.split()
    if len(fields) != 5 or any(not field or any(char not in SCHEDULE_CHARS for char in field) for field in fields):
        raise ValueError('Cron 表达式必须为合法五段格式')
    return ' '.join(fields)


def parse_job_command(command):
    value = str(command or '').strip()
    if not value or '\n' in value or '\r' in value or '`' in value or '$(' in value:
        raise ValueError('命令格式不安全')
    try:
        args = shlex.split(value)
    except ValueError as error:
        raise ValueError('命令引号不匹配') from error
    if not args or args[0] not in ALLOWED_CRON_COMMANDS:
        raise ValueError('命令不在允许列表')
    if len(args) > 64 or any(token in FORBIDDEN_TOKENS for token in args):
        raise ValueError('命令包含不允许的 shell 操作符')
    return args


def command_text(args):
    return shlex.join(list(args))


def _cron_lines(jobs):
    lines = [
        '# Managed by cu-cockpit. Manual edits will be replaced.',
        'SHELL=/bin/sh',
        'PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin',
    ]
    for job in jobs:
        lines.append(f'{job.schedule} root {PYTHON} {MANAGE_PY} run_managed_cron {job.id}')
    return lines


def _validate_cron_lines(lines):
    validation_lines = []
    for line in lines:
        if not line or line.startswith('#') or '=' in line.split()[0]:
            validation_lines.append(line)
            continue
        fields = line.split()
        validation_lines.append(' '.join([*fields[:5], '/usr/bin/true']))
    descriptor, path = tempfile.mkstemp(prefix='cu-cockpit-cron-', text=True)
    try:
        with os.fdopen(descriptor, 'w', encoding='utf-8') as handle:
            handle.write('\n'.join(validation_lines) + '\n')
        result = run_safe(['crontab', '-T', path], {'crontab'}, timeout=5)
        if not result.success:
            raise ValueError(result.stderr.strip() or 'Cron 表达式校验失败')
    finally:
        if os.path.exists(path):
            os.unlink(path)


def _atomic_write_cron(content):
    CRON_FILE.parent.mkdir(parents=True, exist_ok=True)
    descriptor, path = tempfile.mkstemp(prefix='.cu-cockpit.', dir=str(CRON_FILE.parent), text=True)
    try:
        with os.fdopen(descriptor, 'w', encoding='utf-8') as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(path, 0o644)
        os.replace(path, CRON_FILE)
    finally:
        if os.path.exists(path):
            os.unlink(path)


def sync_cron_file():
    jobs = list(CronJob.objects.filter(enabled=True).order_by('id'))
    lines = _cron_lines(jobs)
    _validate_cron_lines(lines)
    _atomic_write_cron('\n'.join(lines) + '\n')


def create_job(payload, actor):
    if not isinstance(payload, dict):
        raise ValueError('请求体必须为对象')
    name = str(payload.get('name') or '').strip()
    if not name or len(name) > 128:
        raise ValueError('任务名称不能为空且不能超过 128 字符')
    schedule = validate_schedule(payload.get('schedule'))
    args = parse_job_command(payload.get('command'))
    enabled = bool(payload.get('enabled', True))
    with transaction.atomic():
        job = CronJob.objects.create(
            name=name,
            schedule=schedule,
            command=args,
            enabled=enabled,
            created_by=actor,
            updated_by=actor,
        )
        sync_cron_file()
    return job


def update_job(job, payload, actor):
    if not isinstance(payload, dict):
        raise ValueError('请求体必须为对象')
    with transaction.atomic():
        if 'name' in payload:
            name = str(payload['name']).strip()
            if not name or len(name) > 128:
                raise ValueError('任务名称不能为空且不能超过 128 字符')
            job.name = name
        if 'schedule' in payload:
            job.schedule = validate_schedule(payload['schedule'])
        if 'command' in payload:
            job.command = parse_job_command(payload['command'])
        if 'enabled' in payload:
            if not isinstance(payload['enabled'], bool):
                raise ValueError('enabled 必须为布尔值')
            job.enabled = payload['enabled']
        job.updated_by = actor
        job.save()
        sync_cron_file()
    return job


def delete_job(job):
    with transaction.atomic():
        job.delete()
        sync_cron_file()


def execute_job(job, actor, manual):
    execution = CronExecution.objects.create(
        job=job,
        job_name=job.name,
        actor=actor,
        manual=manual,
        status='running',
    )
    try:
        result = run_safe(job.command, ALLOWED_CRON_COMMANDS, timeout=60)
        execution.status = 'success' if result.success else 'failed'
        execution.returncode = result.returncode
        execution.stdout = result.stdout
        execution.stderr = result.stderr
        execution.duration_ms = result.duration_ms
    except CommandExecutionTimeout as error:
        execution.status = 'timeout'
        execution.stderr = str(error)
        execution.duration_ms = round(error.timeout * 1000)
    execution.finished_at = timezone.now()
    execution.save()
    job.last_run_at = execution.finished_at
    job.save(update_fields=['last_run_at'])
    return execution


def serialize_job(job):
    return {
        'id': job.id,
        'name': job.name,
        'schedule': job.schedule,
        'command': command_text(job.command),
        'enabled': job.enabled,
        'created_by': job.created_by,
        'updated_by': job.updated_by,
        'created_at': job.created_at,
        'updated_at': job.updated_at,
        'last_run_at': job.last_run_at,
    }


def serialize_execution(execution):
    return {
        'id': execution.id,
        'job_id': execution.job_id,
        'job_name': execution.job_name,
        'actor': execution.actor,
        'manual': execution.manual,
        'status': execution.status,
        'started_at': execution.started_at,
        'finished_at': execution.finished_at,
        'returncode': execution.returncode,
        'stdout': execution.stdout,
        'stderr': execution.stderr,
        'duration_ms': execution.duration_ms,
    }