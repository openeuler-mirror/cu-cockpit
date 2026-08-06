import json
import os
import urllib.request
from dataclasses import dataclass


@dataclass(frozen=True)
class AIProviderConfig:
    base_url: str
    api_key: str
    model: str
    timeout_seconds: float


class AIProviderError(RuntimeError):
    pass


def get_provider_config():
    return AIProviderConfig(
        base_url=os.environ.get('AI_BASE_URL', '').strip().rstrip('/'),
        api_key=os.environ.get('AI_API_KEY', '').strip(),
        model=os.environ.get('AI_MODEL', '').strip(),
        timeout_seconds=float(os.environ.get('AI_TIMEOUT_SECONDS', '30')),
    )


def provider_status(config=None):
    current = config or get_provider_config()
    missing = [
        name for name, value in (
            ('AI_BASE_URL', current.base_url),
            ('AI_API_KEY', current.api_key),
            ('AI_MODEL', current.model),
        ) if not value
    ]
    if missing:
        return {'available': False, 'base_url': current.base_url, 'model': current.model,
                'reason': f'缺少配置: {", ".join(missing)}'}
    return {
        'available': True,
        'base_url': current.base_url,
        'model': current.model,
        'reason': '',
    }


def chat_completion(messages, config=None):
    current = config or get_provider_config()
    status = provider_status(current)
    if not status['available']:
        raise AIProviderError(status['reason'])
    payload = json.dumps({
        'model': current.model,
        'messages': messages,
        'temperature': 0.1,
        'response_format': {'type': 'json_object'},
    }).encode('utf-8')
    request = urllib.request.Request(
        f'{current.base_url}/chat/completions',
        data=payload,
        headers={
            'Authorization': f'Bearer {current.api_key}',
            'Content-Type': 'application/json',
        },
        method='POST',
    )
    try:
        with urllib.request.urlopen(request, timeout=current.timeout_seconds) as response:
            raw_response = response.read(1024 * 1024 + 1)
            if len(raw_response) > 1024 * 1024:
                raise AIProviderError('AI Provider 响应超过 1 MiB 限制')
            data = json.loads(raw_response.decode('utf-8'))
    except (OSError, TimeoutError) as error:
        raise AIProviderError('AI Provider 请求失败') from error
    except (json.JSONDecodeError, UnicodeError) as error:
        raise AIProviderError('AI Provider 响应格式无效') from error
    return data['choices'][0]['message']['content']
