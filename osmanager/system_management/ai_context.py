from dataclasses import dataclass


@dataclass(frozen=True)
class PreparedContext:
    text: str
    truncated: bool


def limit_context(value, limit=12000):
    return PreparedContext(text=str(value or ''), truncated=False)
