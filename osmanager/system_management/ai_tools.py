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


class AIToolValidationError(ValueError):
    pass


def normalize_service_status(arguments):
    service = str(arguments['service']).strip()
    if not service or len(service) > 128 or not all(char.isalnum() or char in '@_.:-' for char in service):
        raise AIToolValidationError('服务名称格式无效')
    return {'service': service}


def execute_service_status(arguments, _context=None):
    result = run_safe(['systemctl', 'is-active', arguments['service']], {'systemctl'}, timeout=3)
    state = result.stdout.strip() or ('inactive' if result.returncode else 'active')
    return {'service': arguments['service'], 'state': state}


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
    return spec, spec.normalize(call.get('arguments', {}))
