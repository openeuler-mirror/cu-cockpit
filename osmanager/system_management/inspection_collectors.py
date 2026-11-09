"""Private fixed-command collectors for offline inspection."""

from .inspection import INSPECTION_TEMPLATE


def _validate_command(args):
    """Accept only exact built-in read-only query shapes."""
    command = tuple(args)
    fixed = (
        ('top', '-bn2', '-d0.2'),
        ('df', '-P', '--', '/'),
        ('df', '-Pi', '--', '/'),
        ('timedatectl', 'show', '--no-pager',
         '--property=NTPSynchronized,NTP,CanNTP'),
    )
    service_prefix = (
        'systemctl', 'show', '--no-pager',
        '--property=LoadState,ActiveState,SubState,Result', '--',
    )
    if command not in fixed and not (
            len(command) == 6 and command[:5] == service_prefix and
            command[5] in INSPECTION_TEMPLATE['registered_services']):
        raise ValueError('Command is not a built-in inspection query')
    return command


def _run_readonly(args, timeout=5):
    """Stream a fixed query; the owning worker supplies process-group isolation."""
    import os
    import selectors
    import subprocess
    import time

    command = _validate_command(args)
    deadline = time.monotonic() + min(timeout, 5)
    process = subprocess.Popen(
        command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, shell=False, close_fds=True,
        env={'PATH': '/usr/sbin:/usr/bin:/sbin:/bin', 'LC_ALL': 'C', 'LANG': 'C'},
    )
    output = bytearray()
    try:
        with selectors.DefaultSelector() as selector:
            selector.register(process.stdout, selectors.EVENT_READ)
            while time.monotonic() < deadline and len(output) <= 16384:
                if not selector.select(max(0, deadline - time.monotonic())):
                    break
                chunk = os.read(process.stdout.fileno(), min(4096, 16385 - len(output)))
                if not chunk:
                    break
                output.extend(chunk)
        if len(output) > 16384:
            raise RuntimeError('Inspection command output exceeds 16 KiB')
        if time.monotonic() >= deadline:
            raise TimeoutError('Inspection command timed out')
        return subprocess.CompletedProcess(
            command, process.wait(timeout=max(0.001, deadline - time.monotonic())),
            stdout=output.decode('utf-8', errors='replace'), stderr='',
        )
    finally:
        if process.poll() is None:
            process.kill()
        process.wait()
        process.stdout.close()


def _metric_runner(args, allowed_commands, timeout=5, evidence=None):
    """Adapt bounded command results to the existing raw metric calculations."""
    import re
    from types import SimpleNamespace

    command = ['top', '-bn2', '-d0.2'] if args[0] == 'top' else args
    result = _run_readonly(command, timeout=timeout)
    stdout = result.stdout
    if args[0] == 'top':
        snapshots = [line for line in stdout.splitlines() if re.search(r'\s*id\b', line)]
        stdout = snapshots[-1] if len(snapshots) >= 2 else ''
    if evidence is not None:
        evidence.update(command=list(result.args), output=result.stdout,
                        returncode=result.returncode)
    return SimpleNamespace(success=result.returncode == 0, stdout=stdout)


def percent_result(value, evidence):
    """Classify a utilization value against the immutable template thresholds."""
    import math

    if (isinstance(value, bool) or not isinstance(value, (int, float)) or
            not math.isfinite(value) or not 0 <= value <= 100):
        raise ValueError('Inspection utilization must be finite and within 0-100')
    warning = INSPECTION_TEMPLATE['warning']
    failure = INSPECTION_TEMPLATE['fail']
    status = 'fail' if value >= failure else 'warning' if value >= warning else 'pass'
    return {
        'status': status, 'value': value, 'unit': '%', 'evidence': evidence,
        'threshold': {'warning': warning, 'fail': failure, 'operator': '>='},
        'reason': f'Utilization {value}%: {status}',
    }
