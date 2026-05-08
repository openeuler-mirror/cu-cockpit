#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import subprocess, os, sys

# 计算boot偏移号
def list_boot_offsets():
    try:
        r = subprocess.run(
            ["journalctl", "--no-pager", "--list-boots"],
            capture_output=True, text=True, check=True,
            env={**os.environ, "SYSTEMD_COLORS": "0"},
        )
    except subprocess.CalledProcessError as e:
        print(e.stderr or "journalctl --list-boots失败", file=sys.stderr)
        return []

    offsets = []
    for line in r.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        first = line.split(None, 1)[0]
        try:
            offsets.append(int(first))
        except ValueError:
            continue
    return offsets

if __name__ == "__main__":
    boot_id=list_boot_offsets()
    print(boot_id)

