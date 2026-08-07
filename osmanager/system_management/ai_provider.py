import json
import os
import urllib.parse
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
    try:
        timeout_seconds = float(os.environ.get('AI_TIMEOUT_SECONDS', '30'))
    except ValueError:
        timeout_seconds = 30.0
    timeout_seconds = max(1.0, min(timeout_seconds, 120.0))
    return AIProviderConfig(
        base_url=os.environ.get('AI_BASE_URL', '').strip().rstrip('/'),
        api_key=os.environ.get('AI_API_KEY', '').strip(),
        model=os.environ.get('AI_MODEL', '').strip(),
        timeout_seconds=timeout_seconds,
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
    parsed_url = urllib.parse.urlparse(current.base_url)
    invalid_url = (
        parsed_url.scheme not in ('http', 'https') or not parsed_url.hostname
        or parsed_url.username is not None or parsed_url.password is not None
        or bool(parsed_url.query) or bool(parsed_url.fragment)
    )
    if invalid_url:
        return {'available': False, 'base_url': '', 'model': current.model,
                'reason': 'AI_BASE_URL 必须为无嵌入凭据的 HTTP(S) 地址'}
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
    try:
        return data['choices'][0]['message']['content']
    except (KeyError, IndexError, TypeError) as error:
        raise AIProviderError('AI Provider 响应结构无效') from error
