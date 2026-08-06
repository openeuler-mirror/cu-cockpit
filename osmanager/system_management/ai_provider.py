from dataclasses import dataclass


@dataclass(frozen=True)
class AIProviderConfig:
    base_url: str
    api_key: str
    model: str
    timeout_seconds: float
