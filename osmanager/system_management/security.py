from collections.abc import Mapping, Sequence


SENSITIVE_MARKERS = ('password', 'passwd', 'private_key', 'privatekey', 'secret', 'token', 'content')
REDACTED = '[REDACTED]'


def sanitize_detail(value, key=''):
    normalized_key = str(key).lower()
    if any(marker in normalized_key for marker in SENSITIVE_MARKERS):
        return REDACTED
    if isinstance(value, Mapping):
        return {str(item_key): sanitize_detail(item_value, item_key) for item_key, item_value in value.items()}
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [sanitize_detail(item) for item in value]
    if isinstance(value, str) and len(value) > 2000:
        return value[:2000] + '...[TRUNCATED]'
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def get_client_ip(request):
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR', '')
    if forwarded:
        return forwarded.split(',', 1)[0].strip() or None
    return request.META.get('HTTP_X_REAL_IP') or request.META.get('REMOTE_ADDR') or None