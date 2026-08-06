import os
from dataclasses import dataclass


@dataclass(frozen=True)
class AIProviderConfig:
    base_url: str
    api_key: str
    model: str
    timeout_seconds: float


def get_provider_config():
    return AIProviderConfig(
        base_url=os.environ.get('AI_BASE_URL', '').strip().rstrip('/'),
        api_key=os.environ.get('AI_API_KEY', '').strip(),
        model=os.environ.get('AI_MODEL', '').strip(),
        timeout_seconds=float(os.environ.get('AI_TIMEOUT_SECONDS', '30')),
    )
