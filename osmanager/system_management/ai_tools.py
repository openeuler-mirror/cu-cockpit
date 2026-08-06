from dataclasses import dataclass
from typing import Callable

from .command import run_safe


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
    return {
        'search': str(arguments.get('search') or '').strip(),
        'limit': int(arguments.get('limit', 20)),
    }


AI_TOOLS = {
    'service.status': AIToolSpec(
        name='service.status', description='查询 systemd 服务运行状态', risk='readonly',
        requires_admin=False, requires_confirmation=True,
        normalize=normalize_service_status, execute=execute_service_status,
        allowed_arguments=('service',),
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
