from dataclasses import dataclass


@dataclass(frozen=True)
class PreparedContext:
    text: str
    truncated: bool
