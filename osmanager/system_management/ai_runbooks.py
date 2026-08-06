from .ai_context import redact_context
from .ai_tools import AIToolExecutionContext, AIToolValidationError, execute_tool_call, normalize_tool_call


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


def current_runbook_step(runbook):
    if runbook.status in ('completed', 'cancelled'):
        raise AIRunbookError('Runbook 已经结束')
    return runbook.steps.filter(position=runbook.current_step).first()


def issue_step_confirmation(step):
    import hashlib
    import secrets
    token = secrets.token_urlsafe(32)
    step.status = 'awaiting_confirmation'
    step.confirmation_token_hash = hashlib.sha256(token.encode('utf-8')).hexdigest()
    step.save(update_fields=['status', 'confirmation_token_hash'])
    return token


def consume_step_confirmation(step, token):
    import hashlib
    import hmac
    if step.status != 'awaiting_confirmation' or not step.confirmation_token_hash:
        raise AIRunbookError('步骤当前不等待确认')
    candidate = hashlib.sha256(str(token).encode('utf-8')).hexdigest()
    if not hmac.compare_digest(candidate, step.confirmation_token_hash):
        raise AIRunbookError('步骤确认令牌无效')
    from django.utils import timezone
    step.status = 'pending'
    step.confirmation_token_hash = ''
    step.confirmed_at = timezone.now()
    step.save(update_fields=['status', 'confirmation_token_hash', 'confirmed_at'])
    return step


def execute_runbook_step(step, actor, is_admin):
    if step.status != 'pending' or (step.risk != 'readonly' and step.confirmed_at is None):
        raise AIRunbookError('步骤未处于可执行状态或尚未确认')
    from django.utils import timezone
    step.status = 'running'
    step.started_at = timezone.now()
    step.save(update_fields=['status', 'started_at'])
    context = AIToolExecutionContext(actor=actor, is_admin=is_admin, confirmed=True)
    try:
        result = execute_tool_call(step.tool_call, context)
    except Exception as error:
        step.status = 'failed'
        step.output = {}
        step.error = redact_context(str(error))[:2000]
        step.finished_at = timezone.now()
        step.save(update_fields=['status', 'output', 'error', 'finished_at'])
        raise
    step.status = 'succeeded'
    step.output = result
    step.error = ''
    step.finished_at = timezone.now()
    step.save(update_fields=['status', 'output', 'error', 'finished_at'])
    return result


def complete_runbook(runbook):
    runbook.status = 'completed'
    runbook.error = ''
    runbook.save(update_fields=['status', 'error', 'updated_at'])
    return runbook
