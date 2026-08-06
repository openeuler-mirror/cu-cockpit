from dataclasses import dataclass
from typing import Callable

from .command import run_safe
from .processes import list_processes


@dataclass(frozen=True)
class AIToolSpec:
    name: str
    description: str
    risk: str
    requires_admin: bool
    requires_confirmation: bool
    normalize: Callable
    execute: Callable
    allowed_arguments: tuple[str, ...] = ()


@dataclass(frozen=True)
class AIToolExecutionContext:
    actor: str
    is_admin: bool
    confirmed: bool


class AIToolValidationError(ValueError):
    pass


def normalize_service_status(arguments):
    service = str(arguments.get('service') or '').strip()
    if not service or len(service) > 128 or not all(char.isalnum() or char in '@_.:-' for char in service):
        raise AIToolValidationError('服务名称格式无效')
    return {'service': service}


def execute_service_status(arguments, _context=None):
    result = run_safe(['systemctl', 'is-active', arguments['service']], {'systemctl'}, timeout=3)
    state = result.stdout.strip() or ('inactive' if result.returncode else 'active')
    return {'service': arguments['service'], 'state': state}


def normalize_process_search(arguments):
    search = str(arguments.get('search') or '').strip()
    try:
        limit = int(arguments.get('limit', 20))
    except (TypeError, ValueError) as error:
        raise AIToolValidationError('进程条数必须为整数') from error
    if len(search) > 128 or not 1 <= limit <= 100:
        raise AIToolValidationError('进程搜索词最多 128 字符且条数范围为 1-100')
    return {'search': search, 'limit': limit}


def execute_process_search(arguments, _context=None):
    return list_processes(
        search=arguments['search'], sort='cpu', order='desc', limit=arguments['limit']
    )


def normalize_listener_search(arguments):
    try:
        port = int(arguments.get('port'))
    except (TypeError, ValueError) as error:
        raise AIToolValidationError('端口必须为整数') from error
    if not 1 <= port <= 65535:
        raise AIToolValidationError('端口范围必须为 1-65535')
    return {'port': port}


AI_TOOLS = {
    'service.status': AIToolSpec(
        name='service.status', description='查询 systemd 服务运行状态', risk='readonly',
        requires_admin=False, requires_confirmation=True,
        normalize=normalize_service_status, execute=execute_service_status,
        allowed_arguments=('service',),
    ),
    'process.search': AIToolSpec(
        name='process.search', description='按名称、用户、PID 或命令搜索进程', risk='readonly',
        requires_admin=False, requires_confirmation=True,
        normalize=normalize_process_search, execute=execute_process_search,
        allowed_arguments=('search', 'limit'),
    ),
}


def get_tool(name):
    try:
        return AI_TOOLS[str(name)]
    except KeyError as error:
        raise AIToolValidationError('工具未注册') from error


def normalize_tool_call(call):
    if not isinstance(call, dict) or not isinstance(call.get('arguments', {}), dict):
        raise AIToolValidationError('工具调用和 arguments 必须为对象')
    spec = get_tool(call['tool'])
    arguments = call.get('arguments', {})
    unknown = sorted(set(arguments) - set(spec.allowed_arguments))
    if unknown:
        raise AIToolValidationError(f'工具包含未知参数: {", ".join(unknown)}')
    return spec, spec.normalize(arguments)


def execute_tool_call(call, context):
    spec, arguments = normalize_tool_call(call)
    if spec.requires_confirmation and not context.confirmed:
        raise AIToolValidationError('工具执行需要用户确认')
    if spec.requires_admin and not context.is_admin:
        raise AIToolValidationError('工具执行需要管理员权限')
    return spec.execute(arguments, context)
