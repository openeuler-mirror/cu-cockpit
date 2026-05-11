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
    if args.identifier:
        cmd += ['-t', args.identifier]
    if args.cursor:
        cmd = ['journalctl', '--no-pager', '--cursor', args.cursor, '-o', 'json', '-n', '1']
    elif args.output_format in ('all_json', 'summary'):
        cmd += ['-o', 'json']
        if args.output_format == 'summary':
            cmd += ['--output-fields', '__REALTIME_TIMESTAMP,MESSAGE,_SYSTEMD_UNIT,UNIT,SYSLOG_IDENTIFIER,_HOSTNAME,__CURSOR']
    if args.debug:
        print(f"执行命令: {' '.join(cmd)}", file=sys.stderr)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False, env={**os.environ, 'SYSTEMD_COLORS': '0', 'TZ': os.environ.get('TZ', 'Asia/Shanghai')})
        if result.returncode == 1 and '-- No entries --' in result.stdout:
            if args.output_format == 'raw':
                print(result.stdout)
            elif args.output_format == 'json':
                print('[]')
            elif args.output_format == 'all_json':
                print('[]')
            elif args.output_format == 'summary':
                print('[]')
            return
        if result.returncode == 1 and (not result.stderr.strip()):
            if args.output_format == 'raw':
                print('')
            elif args.output_format == 'json':
                print('[]')
            elif args.output_format == 'all_json':
                print('[]')
            elif args.output_format == 'summary':
                print('[]')
            return
        if result.returncode != 0:
            error_msg = result.stderr.strip() or 'journalctl返回非0且无错误信息'
            cmd = ' '.join(cmd)
            err = {'error': 'journalctl执行失败', 'returncode': result.returncode, 'cmd': cmd, 'message': error_msg}
            if args.debug:
                err['stdout'] = result.stdout
                err['stderr'] = result.stderr
            print(json.dumps(err, ensure_ascii=False), file=sys.stderr)
            sys.exit(result.returncode)
        if args.output_format == 'raw':
            print(result.stdout)
        elif args.output_format == 'json':
            logs = []
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    parsed_log = parse_log_line(line)
                    logs.append(parsed_log)
            print(json.dumps(logs, indent=2, ensure_ascii=False))
        elif args.output_format == 'all_json':
            logs = []
            for line in result.stdout.splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    logs.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
            print(json.dumps(logs, indent=2, ensure_ascii=False))
        elif args.output_format == 'summary':
            logs = []
            for line in result.stdout.splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    full_log = json.loads(line)
                    logs.append(extract_summary_fields(full_log))
                except json.JSONDecodeError:
                    pass
            print(json.dumps(logs, indent=2, ensure_ascii=False))
    except FileNotFoundError:
        print('未找到journalctl', file=sys.stderr)
        sys.exit(127)
    except subprocess.CalledProcessError as e:
        sys.exit(e.returncode)
if __name__ == '__main__':
    main()
