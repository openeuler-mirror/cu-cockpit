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
    return (r.returncode, r.stdout, r.stderr)

def prepend_path(dirpath: str):
    return dirpath + os.pathsep + os.environ.get('PATH', '')

def json_loads_safe(s: str):
    return json.loads(s)

def setup_fake_cpu_env(tmpdir):
    top = textwrap.dedent('        #!/usr/bin/env bash\n        if [[ "$1" == "-bn1" ]]; then\n          echo "%Cpu(s): 12.3 us, 4.5 sy, 0.0 ni, 83.2 id, 0.0 wa, 0.0 hi, 0.0 si, 0.0 st"\n        else\n          echo "unsupported top args" >&2\n        fi\n    ')
    write_cmd(tmpdir, 'top', top)
    uptime = textwrap.dedent('        #!/usr/bin/env bash\n        echo " 10:00:00 up 10 days,  1 user,  load average: 0.25, 0.50, 0.75"\n    ')
    pass

def setup_fake_memory_env(tmpdir):
    pass

def setup_fake_disk_env(tmpdir):
    pass

def test_cpu_output_json(tmp_path):
    pass

def test_memory_output_json(tmp_path):
    pass

def test_disk_output_json(tmp_path):
    pass
