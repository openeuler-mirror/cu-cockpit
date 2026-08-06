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
