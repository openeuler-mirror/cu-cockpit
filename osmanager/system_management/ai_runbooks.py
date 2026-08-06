from .ai_tools import AIToolValidationError, normalize_tool_call


class AIRunbookError(ValueError):
    pass


def normalize_runbook_payload(payload):
    if not isinstance(payload, dict) or set(payload) != {'title', 'steps'} or not isinstance(payload['steps'], list):
        raise AIRunbookError('Runbook 必须包含 title 和 steps')
    title = str(payload['title'] or '').strip()
    if not title or len(title) > 256 or not 1 <= len(payload['steps']) <= 20:
        raise AIRunbookError('Runbook 标题或步骤数量无效')
    steps = []
    for position, item in enumerate(payload['steps']):
        if not isinstance(item, dict) or set(item) != {'title', 'tool_call'}:
            raise AIRunbookError('Runbook 步骤结构无效')
        step_title = str(item['title'] or '').strip()
        if not step_title or len(step_title) > 256:
            raise AIRunbookError('Runbook 步骤标题无效')
        try:
            spec, arguments = normalize_tool_call(item['tool_call'])
        except AIToolValidationError as error:
            raise AIRunbookError(str(error)) from error
        steps.append({
            'position': position,
            'title': step_title,
            'tool_call': {'tool': spec.name, 'arguments': arguments},
            'risk': spec.risk,
        })
    return {'title': title, 'steps': steps}


def create_runbook(payload, actor):
    from django.db import transaction
    from .models import AIRunbook, AIRunbookStep
    normalized = normalize_runbook_payload(payload)
    with transaction.atomic():
        runbook = AIRunbook.objects.create(actor=actor, title=normalized['title'])
        AIRunbookStep.objects.bulk_create(
            AIRunbookStep(runbook=runbook, **step) for step in normalized['steps']
        )
    return runbook


def require_runbook_owner(runbook, actor):
    if runbook.actor != actor:
        raise AIRunbookError('无权操作其他用户的 Runbook')
    return runbook
