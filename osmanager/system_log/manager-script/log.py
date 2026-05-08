import argparse
import subprocess
import os
import sys
import json
import re
from datetime import datetime

def parse_log_line(line):
    """解析单行日志为结构化数据"""
    pattern = '^(\\w{3})\\s+(\\d{1,2})\\s+(\\d{2}:\\d{2}:\\d{2})\\s+(\\S+)\\s+(\\S+)\\[(\\d+)\\]:\\s+(.*)$'
    match = re.match(pattern, line.strip())
    if match:
        month, day, time, hostname, service, pid, message = match.groups()
        return {'date': f'{month} {day}', 'time': time, 'hostname': hostname, 'service': service, 'pid': int(pid), 'message': message, 'raw': line.strip()}
    return {'date': '', 'time': '', 'hostname': '', 'service': '', 'pid': 0, 'message': line.strip(), 'raw': line.strip()}

def extract_summary_fields(log_entry):
    """从完整日志条目中提取摘要字段（用于列表快速渲染）。"""
    return {'timestamp': log_entry.get('__REALTIME_TIMESTAMP', ''), 'message': log_entry.get('MESSAGE', ''), 'service': log_entry.get('_SYSTEMD_UNIT', log_entry.get('UNIT', '')), 'identifier': log_entry.get('SYSLOG_IDENTIFIER', ''), 'hostname': log_entry.get('_HOSTNAME', ''), 'cursor': log_entry.get('__CURSOR', '')}

def main():
    parser = argparse.ArgumentParser(description='按时间/优先级/服务名过滤systemd日志（默认最近24h、err级别、倒序）')
    parser.add_argument('--since', help="开始时间，如 '2025-09-01 10:00:00' 或 '1h ago'；默认 '24h ago'")
    parser.add_argument('--until', help="结束时间，如 '2025-09-01 12:00:00' 或 'now'")
    parser.add_argument('--priority', '-p', help="优先级，如 'err', 'info', '0..3'；默认 'err'")
    pass
if __name__ == '__main__':
    main()
