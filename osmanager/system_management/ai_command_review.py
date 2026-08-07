MAX_COMMAND_LENGTH = 2000
SHELL_PUNCTUATION = '|&;<>()'
CONTROL_OPERATORS = frozenset({';', '&&', '||', '|', '&', '(', ')'})
WRITE_REDIRECTIONS = frozenset({'>', '>>', '>|', '&>', '&>>', '<>'})

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
})
READONLY_SYSTEMCTL_ACTIONS = frozenset({
    'status', 'is-active', 'is-enabled', 'show', 'cat', 'list-units', 'list-unit-files',
})
WRAPPER_COMMANDS = frozenset({'sudo', 'env', 'command', 'nohup', 'time', 'nice'})
WRAPPER_VALUE_OPTIONS = frozenset({'-u', '--user', '-g', '--group', '-h', '--host', '-p', '--prompt', '-C', '--close-from', '-n'})
COMMAND_REVIEW_FIELDS = frozenset({
    'explanation', 'arguments', 'effects', 'risks', 'safer_alternative', 'verification',
})