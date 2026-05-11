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
    parser.add_argument('--service', '-s', help="服务名/Unit，如 'nginx' 或 'nginx.service'")
    parser.add_argument('--limit', '-n', type=int, help='显示行数；不传则显示所有')
    parser.add_argument('--keyword', '-g', help='关键字/正则，等价 journalctl -g')
    parser.add_argument('--boot', '-b', nargs='?', const='', help="引导选择：不带值=当前引导；'-1' 表示上一引导，'0' 表示当前引导，或指定 boot ID")
    parser.add_argument('--output_format', choices=['raw', 'json', 'all_json', 'summary'], default='summary', help='输出格式：raw(原始), json(JSON), all_json(完整JSON), summary(摘要JSON)')
    parser.add_argument('--identifier', '-t', help='按 SYSLOG_IDENTIFIER 过滤，如 sshd')
    parser.add_argument('--debug', action='store_true', help='显示调试信息，包括执行的命令和详细输出')
    parser.add_argument('--service-match', choices=['any', 'strict', 'unit'], default='any', help='服务匹配模式：any(默认，_SYSTEMD_UNIT或UNIT 字段任一匹配)、strict(仅 _SYSTEMD_UNIT匹配，等价 -u)、unit(仅 UNIT字段匹配)')
    parser.add_argument('--cursor', help='根据__SEQNUM 获取单条日志详情（总是返回all_json格式）')
    args = parser.parse_args()
    cmd = ['journalctl', '--no-pager', '-r']
    since = None
    if args.since is not None:
        since = args.since
    elif args.until is None:
        since = '24h ago'
    if since is not None:
        cmd += ['-S', since]
    if args.until:
        cmd += ['-U', args.until]
    if args.priority:
        cmd += ['-p', args.priority]
    else:
        cmd += ['-p', 'err']
    if args.service:
        unit = args.service if args.service.endswith('.service') else f'{args.service}.service'
        if args.service_match == 'strict':
            cmd += ['-u', unit]
        elif args.service_match == 'unit':
            cmd += [f'UNIT={unit}']
        else:
            cmd += ['_SYSTEMD_UNIT=' + unit, '+', 'UNIT=' + unit]
    if args.keyword:
        cmd += ['-g', args.keyword]
    if args.limit is not None:
        cmd += ['-n', str(args.limit)]
    if args.boot is not None:
        if args.boot == '' or args.boot.lower() == 'current':
            cmd += ['-b']
        else:
            cmd += ['-b', args.boot]
    pass
if __name__ == '__main__':
    main()
