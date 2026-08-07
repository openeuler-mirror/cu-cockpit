import ipaddress
from collections.abc import Mapping, Sequence


SENSITIVE_MARKERS = (
    'password', 'passwd', 'private_key', 'privatekey', 'secret', 'token', 'content',
    'authorization', 'cookie', 'session',
)
REDACTED = '[REDACTED]'
MAX_DETAIL_STRING_LENGTH = 2000


def sanitize_detail(value, key=''):
    normalized_key = str(key).lower()
    if any(marker in normalized_key for marker in SENSITIVE_MARKERS):
        return REDACTED
    if isinstance(value, Mapping):
        return {str(item_key): sanitize_detail(item_value, item_key) for item_key, item_value in value.items()}
    if isinstance(value, (bytes, bytearray)):
        return f'[BINARY {len(value)} bytes]'
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [sanitize_detail(item) for item in value]
    if isinstance(value, str) and len(value) > MAX_DETAIL_STRING_LENGTH:
        return value[:MAX_DETAIL_STRING_LENGTH] + '...[TRUNCATED]'
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def get_client_ip(request):
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR', '')
    if forwarded:
        candidate = forwarded.split(',', 1)[0].strip()
    else:
        candidate = request.META.get('HTTP_X_REAL_IP') or request.META.get('REMOTE_ADDR') or ''
    try:
        return str(ipaddress.ip_address(candidate))
    except ValueError:
        return None
