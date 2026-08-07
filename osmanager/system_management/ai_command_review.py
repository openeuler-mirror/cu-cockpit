import os
import shlex

from .ai_analysis import AIAnalysisError


MAX_COMMAND_LENGTH = 2000
SHELL_PUNCTUATION = '|&;<>()'
CONTROL_OPERATORS = frozenset({';', '&&', '||', '|', '&', '(', ')'})
WRITE_REDIRECTIONS = frozenset({'>', '>>', '>|', '&>', '&>>', '<>'})
REDIRECTION_OPERATORS = WRITE_REDIRECTIONS | frozenset({'<', '<<', '<<<'})

DANGEROUS_COMMANDS = frozenset({
    'rm', 'dd', 'wipefs', 'fdisk', 'parted', 'shutdown', 'reboot', 'poweroff', 'halt',
})
CHANGE_COMMANDS = frozenset({
    'chmod', 'chown', 'chgrp', 'cp', 'mv', 'install', 'ln', 'touch', 'truncate', 'tee',
    'mount', 'umount', 'useradd', 'usermod', 'userdel', 'groupadd', 'groupmod',
    'groupdel', 'passwd', 'dnf', 'yum', 'rpm', 'apt', 'apt-get', 'dpkg', 'crontab',
    'firewall-cmd', 'iptables', 'nft', 'sysctl', 'kill', 'pkill', 'killall',
})
READONLY_COMMANDS = frozenset({
    'ls', 'pwd', 'whoami', 'id', 'uname', 'uptime', 'free', 'df', 'du', 'ps', 'pgrep',
    'ss', 'netstat', 'lsof', 'dmesg', 'cat', 'head', 'tail', 'wc', 'stat', 'readlink',
    'realpath', 'which', 'whereis', 'printenv', 'grep', 'awk', 'sort', 'uniq', 'cut', 'tr',
    'echo', 'printf', 'true', 'false', 'test',
})
READONLY_SYSTEMCTL_ACTIONS = frozenset({
    'status', 'is-active', 'is-enabled', 'show', 'cat', 'list-units', 'list-unit-files',
})
WRAPPER_COMMANDS = frozenset({'sudo', 'env', 'command', 'nohup', 'time', 'nice'})
WRAPPER_VALUE_OPTIONS = frozenset({'-u', '--user', '-g', '--group', '-h', '--host', '-p', '--prompt', '-C', '--close-from', '-n'})
COMMAND_REVIEW_FIELDS = frozenset({
    'explanation', 'arguments', 'effects', 'risks', 'safer_alternative', 'verification',
})


def validate_linux_command(command):
    if not isinstance(command, str) or not command.strip():
        raise AIAnalysisError('Linux 命令必须为非空字符串')
    if '\x00' in command:
        raise AIAnalysisError('Linux 命令不能包含 NUL 字节')
    if len(command) > MAX_COMMAND_LENGTH:
        raise AIAnalysisError(f'Linux 命令不能超过 {MAX_COMMAND_LENGTH} 字符')
    return command.strip()


def parse_linux_command(command):
    text = validate_linux_command(command)
    source = text.replace('\r\n', '\n').replace('\r', '\n').replace('\n', ' ; ')
    lexer = shlex.shlex(source, posix=True, punctuation_chars=SHELL_PUNCTUATION)
    lexer.whitespace_split = True
    lexer.commenters = ''
    try:
        tokens = list(lexer)
    except ValueError as error:
        raise AIAnalysisError('Linux 命令语法无法解析') from error
    segments = []
    operators = []
    current = []
    for token in tokens:
        is_operator = token in CONTROL_OPERATORS or token in REDIRECTION_OPERATORS
        is_operator = is_operator or (token and all(char in SHELL_PUNCTUATION for char in token))
        if is_operator:
            operators.append(token)
        if is_operator and token not in REDIRECTION_OPERATORS:
            if current:
                segments.append(current)
                current = []
            continue
        current.append(token)
    if current:
        segments.append(current)
    return {'segments': segments, 'operators': operators}


def extract_segment_command(segment):
    wrappers = []
    index = 0
    while index < len(segment):
        token = segment[index]
        if token in REDIRECTION_OPERATORS:
            break
        assignment = token.split('=', 1)[0]
        if '=' in token and assignment.isidentifier():
            index += 1
            continue
        name = os.path.basename(token).lower()
        if name in WRAPPER_COMMANDS:
            wrappers.append(name)
            index += 1
            while index < len(segment) and segment[index].startswith('-'):
                option = segment[index].split('=', 1)[0]
                index += 1
                if option in WRAPPER_VALUE_OPTIONS and index < len(segment):
                    index += 1
            continue
        if token == '$':
            index += 1
            continue
        arguments = []
        for argument in segment[index + 1:]:
            if argument in REDIRECTION_OPERATORS:
                break
            arguments.append(argument)
        return {'name': name, 'arguments': arguments, 'wrappers': wrappers}
    return {'name': '', 'arguments': [], 'wrappers': wrappers}


def classify_segment_risk(segment):
    command = extract_segment_command(segment)
    name = command['name']
    arguments = command['arguments']
    if not name:
        return {**command, 'risk': 'change', 'reason': '无法识别命令段，按变更风险处理'}
    if name in DANGEROUS_COMMANDS or name == 'mkfs' or name.startswith('mkfs.'):
        return {**command, 'risk': 'dangerous', 'reason': f'{name} 属于破坏性命令'}
    if name in {'kill', 'pkill', 'killall'} and any(value in ('-9', '-KILL') for value in arguments):
        return {**command, 'risk': 'dangerous', 'reason': f'{name} 请求不可恢复的强制终止'}
    if name == 'systemctl':
        action = next((value for value in arguments if not value.startswith('-')), '')
        risk = 'readonly' if action in READONLY_SYSTEMCTL_ACTIONS else 'change'
        return {**command, 'risk': risk, 'reason': f'systemctl {action or "未知动作"}'}
    if name == 'service':
        risk = 'readonly' if arguments and arguments[-1] == 'status' else 'change'
        return {**command, 'risk': risk, 'reason': f'service {arguments[-1] if arguments else "未知动作"}'}
    if name == 'sed':
        changed = any(value == '-i' or value.startswith('-i') for value in arguments)
        return {**command, 'risk': 'change' if changed else 'readonly', 'reason': 'sed 原地写入' if changed else 'sed 只读转换'}
    if name == 'find':
        changed = any(value in ('-delete', '-exec', '-execdir', '-ok', '-okdir') for value in arguments)
        return {**command, 'risk': 'change' if changed else 'readonly', 'reason': 'find 包含写操作' if changed else 'find 只读查询'}
    if name == 'journalctl':
        changed = any(value.startswith(('--vacuum', '--rotate', '--flush', '--sync')) for value in arguments)
        return {**command, 'risk': 'change' if changed else 'readonly', 'reason': 'journalctl 修改日志存储' if changed else 'journalctl 只读查询'}
    if name in CHANGE_COMMANDS:
        return {**command, 'risk': 'change', 'reason': f'{name} 可能修改系统状态'}
    if name in READONLY_COMMANDS:
        return {**command, 'risk': 'readonly', 'reason': f'{name} 是已知只读命令'}
    return {**command, 'risk': 'change', 'reason': f'未识别命令 {name}，按变更风险处理'}


def assess_linux_command(command):
    parsed = parse_linux_command(command)
    details = [classify_segment_risk(segment) for segment in parsed['segments']]
    risks = {detail['risk'] for detail in details}
    if 'dangerous' in risks:
        risk = 'dangerous'
    elif 'change' in risks:
        risk = 'change'
    else:
        risk = 'readonly'
    reasons = [detail['reason'] for detail in details]
    if any(operator in WRITE_REDIRECTIONS for operator in parsed['operators']):
        if risk == 'readonly':
            risk = 'change'
        reasons.append('包含写重定向，可能修改文件或设备')
    control = [operator for operator in parsed['operators'] if operator not in REDIRECTION_OPERATORS]
    if control:
        reasons.append('包含复合 Shell 控制操作符，已逐段检查')
    if not details:
        risk = 'change'
        reasons.append('未找到可识别命令，按变更风险处理')
    commands = [detail['name'] for detail in details if detail['name']]
    wrappers = [wrapper for detail in details for wrapper in detail['wrappers']]
    return {
        'risk': risk,
        'reasons': list(dict.fromkeys(reasons)),
        'commands': list(dict.fromkeys(commands)),
        'operators': list(dict.fromkeys(parsed['operators'])),
        'wrappers': list(dict.fromkeys(wrappers)),
        'requires_admin_review': risk != 'readonly',
    }


def validate_command_review_analysis(analysis):
    if not isinstance(analysis, dict) or set(analysis) != COMMAND_REVIEW_FIELDS:
        raise AIAnalysisError('AI 命令解释字段无效')
    if not isinstance(analysis['explanation'], str) or not analysis['explanation'].strip():
        raise AIAnalysisError('AI 命令解释不能为空')
    if not isinstance(analysis['safer_alternative'], str):
        raise AIAnalysisError('AI 安全替代方案必须为字符串')
    if len(analysis['explanation']) > 4000 or len(analysis['safer_alternative']) > 2000:
        raise AIAnalysisError('AI 命令解释文本超过限制')
    normalized = {
        'explanation': analysis['explanation'].strip(),
        'safer_alternative': analysis['safer_alternative'].strip(),
    }
    for field in ('arguments', 'effects', 'risks', 'verification'):
        values = analysis[field]
        if not isinstance(values, list) or len(values) > 20:
            raise AIAnalysisError(f'AI 命令解释字段 {field} 必须为不超过 20 项的数组')
        if any(not isinstance(value, str) or len(value) > 500 for value in values):
            raise AIAnalysisError(f'AI 命令解释字段 {field} 内容无效')
        normalized[field] = [value.strip() for value in values if value.strip()]
    return normalized