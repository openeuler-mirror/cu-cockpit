from .ai_tools import normalize_tool_call


class AIRunbookError(ValueError):
    pass


def normalize_runbook_payload(payload):
    steps = []
    for position, item in enumerate(payload['steps']):
        spec, arguments = normalize_tool_call(item['tool_call'])
        steps.append({
            'position': position,
            'title': str(item['title']).strip(),
            'tool_call': {'tool': spec.name, 'arguments': arguments},
            'risk': spec.risk,
        })
    return {'title': str(payload['title']).strip(), 'steps': steps}
