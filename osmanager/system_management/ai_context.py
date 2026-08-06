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
    return pattern.sub(lambda match: f'{match.group(1)}=[REDACTED]', str(value or ''))
