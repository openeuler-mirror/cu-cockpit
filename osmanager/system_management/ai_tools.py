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
    ),
}


def get_tool(name):
    return AI_TOOLS[name]
