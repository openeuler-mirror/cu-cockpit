from dataclasses import dataclass
from typing import Callable


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
