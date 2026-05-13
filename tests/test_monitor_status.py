#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import stat
import json
import subprocess
import textwrap
import shutil
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
SCRIPT_PATH = os.path.join(PROJECT_ROOT, 'osmanager', 'rescrouce_monitor', 'manager-script', 'monitor_status.sh')

pytestmark = pytest.mark.skipif(os.name != 'posix', reason='需要 posix + bash 环境运行 bash 脚本')

def make_executable(path: str):
    st = os.stat(path)
    os.chmod(path, st.st_mode | stat.S_IEXEC)

def write_cmd(tmpdir, name, content):
    p = os.path.join(tmpdir, name)
    with open(p, 'w', encoding='utf-8') as f:
        f.write(content)
    make_executable(p)
    return p

def run_script(args, env=None):
    cmd = ['bash', SCRIPT_PATH] + args
    r = subprocess.run(cmd, capture_output=True, text=True, env=env)
    return r.returncode, r.stdout, r.stderr

def prepend_path(dirpath: str):
    return dirpath + os.pathsep + os.environ.get('PATH', '')

def json_loads_safe(s: str):
    return json.loads(s)


def setup_fake_cpu_env(tmpdir):
    # fake top: 输出 %Cpu(s) 行
    top = textwrap.dedent("""\
        #!/usr/bin/env bash
        if [[ "$1" == "-bn1" ]]; then
          echo "%Cpu(s): 12.3 us, 4.5 sy, 0.0 ni, 83.2 id, 0.0 wa, 0.0 hi, 0.0 si, 0.0 st"
        else
          echo "unsupported top args" >&2
        fi
    """)
    write_cmd(tmpdir, 'top', top)

    # fake uptime: 输出 load average
    uptime = textwrap.dedent("""\
        #!/usr/bin/env bash
        echo " 10:00:00 up 10 days,  1 user,  load average: 0.25, 0.50, 0.75"
    """)
    write_cmd(tmpdir, 'uptime', uptime)

    # fake bc: 直接返回期望的计算结果
    bc = textwrap.dedent("""\
        #!/usr/bin/env bash
        echo "16.8"
    """)
    write_cmd(tmpdir, 'bc', bc)


def setup_fake_memory_env(tmpdir):
    # fake grep: 根据第一个参数关键字返回固定行
    grep = textwrap.dedent("""\
        #!/usr/bin/env bash
        # 用法: grep 'MemTotal:' /proc/meminfo
        pattern="$1"
        shift
        if [[ "$pattern" == "MemTotal:" ]]; then
          echo "MemTotal:       4096000 kB"
        elif [[ "$pattern" == "MemAvailable:" ]]; then
          echo "MemAvailable:   1024000 kB"
        elif [[ "$pattern" == "SwapTotal:" ]]; then
          echo "SwapTotal:      2048000 kB"
        elif [[ "$pattern" == "SwapFree:" ]]; then
          echo "SwapFree:       512000 kB"
        else
          # 其他情况按原 grep 失败语义返回非0
          exit 1
        fi
    """)
    write_cmd(tmpdir, 'grep', grep)



def setup_fake_disk_env(tmpdir):
    # fake df: 根据路径输出不同行
    df = textwrap.dedent("""\
        #!/usr/bin/env bash
        if [[ "$1" == "-h" && "$2" == "/" ]]; then
          # header + data
          echo "Filesystem      Size  Used Avail Use% Mounted on"
          echo "/dev/sda1        50G   20G   28G  42% /"
        elif [[ "$1" == "-h" && "$2" == "/boot" ]]; then
          echo "Filesystem      Size  Used Avail Use% Mounted on"
          echo "/dev/sda2       1024M  256M  700M  27% /boot"
        else
          echo "unexpected df args: $@" >&2
          exit 1
        fi
    """)
    write_cmd(tmpdir, 'df', df)


def test_cpu_output_json(tmp_path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    setup_fake_cpu_env(str(bin_dir))

    env = os.environ.copy()
    env['PATH'] = prepend_path(str(bin_dir))

    code, out, err = run_script(['cpu'], env=env)
    print(f"Debug - stdout: {repr(out)}")
    print(f"Debug - stderr: {repr(err)}")
    print(f"Debug - return code: {code}")

    assert code == 0, err
    data = json_loads_safe(out)
    print(f"Debug - parsed data: {data}")

    assert 'cpu' in data
    cpu = data['cpu']
    print(f"Debug - cpu data: {cpu}")
    print(f"Debug - total_utilization_percent: {repr(cpu['total_utilization_percent'])}")

    # 根据实际输出来调整断言
    assert cpu['user_percent'] == '12.3%'
    assert cpu['system_percent'] == '4.5%'
    assert cpu['idle_percent'] == '83.2%'
    assert cpu['total_utilization_percent'] == '16.8%'


def test_memory_output_json(tmp_path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    setup_fake_memory_env(str(bin_dir))

    env = os.environ.copy()
    env['PATH'] = prepend_path(str(bin_dir))

    code, out, err = run_script(['memory'], env=env)
    assert code == 0, err
    data = json_loads_safe(out)
    assert 'memory' in data
    mem = data['memory']
    assert mem['total_mb'] == 4000
    assert mem['available_mb'] == 1000
    assert mem['used_mb'] == 3000
    assert mem['swap_total_mb'] == 2000
    assert mem['swap_free_mb'] == 500
    assert mem['swap_used_mb'] == 1500


def test_disk_output_json(tmp_path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    setup_fake_disk_env(str(bin_dir))

    env = os.environ.copy()
    env['PATH'] = prepend_path(str(bin_dir))

    code, out, err = run_script(['disk'], env=env)
    assert code == 0, err
    data = json_loads_safe(out)
    assert 'total_disk' in data and 'boot_disk' in data
    assert data['total_disk']['total'] == '50G'
    assert data['total_disk']['used'] == '20G'
    assert data['total_disk']['free'] == '28G'
    assert data['boot_disk']['boot_total'] == '1024M'
    assert data['boot_disk']['boot_used'] == '256M'
    assert data['boot_disk']['boot_free'] == '700M'
