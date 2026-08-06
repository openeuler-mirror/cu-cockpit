import re
from dataclasses import dataclass


@dataclass(frozen=True)
class PreparedContext:
    text: str
    truncated: bool


def limit_context(value, limit=12000):
    text = str(value or '')
    if len(text) > limit:
        return PreparedContext(text=text[:limit], truncated=True)
    return PreparedContext(text=text, truncated=False)


def redact_context(value):
    pattern = re.compile(
        r'(?i)\b(password|passwd|token|api[_-]?key|secret)\s*[:=]\s*(?:"[^"]*"|\'[^\']*\'|[^\s,;]+)'
    )
    redacted = pattern.sub(lambda match: f'{match.group(1)}=[REDACTED]', str(value or ''))
    return re.sub(
        r'-----BEGIN (?:[A-Z0-9]+ )?PRIVATE KEY-----.*?-----END (?:[A-Z0-9]+ )?PRIVATE KEY-----',
        '[REDACTED PRIVATE KEY]',
        redacted,
        flags=re.DOTALL,
    )
