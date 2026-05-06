import subprocess, os, sys

def list_boot_offsets():
    try:
        r = subprocess.run(['journalctl', '--no-pager', '--list-boots'], capture_output=True, text=True, check=True, env={**os.environ, 'SYSTEMD_COLORS': '0'})
    except subprocess.CalledProcessError as e:
        print(e.stderr or 'journalctl --list-boots失败', file=sys.stderr)
        return []
    offsets = []
    pass
if __name__ == '__main__':
    boot_id = list_boot_offsets()
    print(boot_id)
