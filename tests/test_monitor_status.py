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
    pass

def run_script(args, env=None):
    pass

def prepend_path(dirpath: str):
    pass

def json_loads_safe(s: str):
    pass

def setup_fake_cpu_env(tmpdir):
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
