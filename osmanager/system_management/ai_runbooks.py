from .ai_context import redact_context
import json

from .ai_tools import (
    AIToolExecutionContext,
    AIToolValidationError,
    execute_tool_call,
    normalize_tool_call,
    tool_catalog,
)


class AIRunbookError(ValueError):
    pass


def build_runbook_messages(request_text):
    catalog = json.dumps(tool_catalog(), ensure_ascii=False)
    system = (
        '你是 cu-cockpit 受控 Runbook 规划器。只能使用工具目录中的注册工具，最多 20 步；'
        '不得生成原始 Shell、管道、重定向或命令替换。只返回 JSON 对象：'
        '{"title":"标题","steps":[{"title":"步骤","tool_call":'
        '{"tool":"注册工具名","arguments":{}}}]}。工具目录：' + catalog
    )
    return [
        {'role': 'system', 'content': system},
        {'role': 'user', 'content': str(request_text)},
    ]


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


def pause_runbook_for_confirmation(runbook, step):
    token = issue_step_confirmation(step)
    runbook.status = 'paused'
    runbook.error = ''
    runbook.save(update_fields=['status', 'error', 'updated_at'])
    return token


def fail_runbook(runbook, error):
    runbook.status = 'failed'
    runbook.error = redact_context(str(error))[:2000]
    runbook.save(update_fields=['status', 'error', 'updated_at'])
    return runbook


def advance_runbook_position(runbook):
    runbook.current_step += 1
    if runbook.steps.filter(position=runbook.current_step).exists():
        runbook.status = 'running'
        runbook.error = ''
        runbook.save(update_fields=['current_step', 'status', 'error', 'updated_at'])
        return False
    complete_runbook(runbook)
    runbook.save(update_fields=['current_step', 'updated_at'])
    return True


def advance_runbook(runbook, actor, is_admin):
    require_runbook_owner(runbook, actor)
    step = current_runbook_step(runbook)
    if step is None:
        complete_runbook(runbook)
        return {'action': 'completed', 'step': None, 'result': None}
    if step.risk != 'readonly' and step.confirmed_at is None:
        if step.status == 'awaiting_confirmation':
            return {
                'action': 'confirmation_required',
                'step': step,
                'confirmation_token': None,
                'result': None,
            }
        if step.status != 'pending':
            raise AIRunbookError('写步骤已经等待确认')
        token = pause_runbook_for_confirmation(runbook, step)
        return {
            'action': 'confirmation_required',
            'step': step,
            'confirmation_token': token,
            'result': None,
        }
    try:
        result = execute_runbook_step(step, actor, is_admin)
    except Exception as error:
        fail_runbook(runbook, error)
        raise
    completed = advance_runbook_position(runbook)
    return {
        'action': 'completed' if completed else 'executed',
        'step': step,
        'result': result,
    }


def confirm_runbook_step(runbook, actor, token):
    require_runbook_owner(runbook, actor)
    step = current_runbook_step(runbook)
    if step is None:
        raise AIRunbookError('Runbook 没有待确认步骤')
    consume_step_confirmation(step, token)
    runbook.status = 'running'
    runbook.error = ''
    runbook.save(update_fields=['status', 'error', 'updated_at'])
    return step


def retry_runbook_step(runbook, actor):
    require_runbook_owner(runbook, actor)
    step = current_runbook_step(runbook)
    if runbook.status != 'failed' or step is None or step.status != 'failed':
        raise AIRunbookError('当前 Runbook 步骤不可重试')
    step.status = 'pending'
    step.output = {}
    step.error = ''
    step.confirmed_at = None
    step.started_at = None
    step.finished_at = None
    step.save(update_fields=['status', 'output', 'error', 'confirmed_at', 'started_at', 'finished_at'])
    runbook.status = 'running'
    runbook.error = ''
    runbook.save(update_fields=['status', 'error', 'updated_at'])
    return step


def skip_runbook_step(runbook, actor):
    require_runbook_owner(runbook, actor)
    step = current_runbook_step(runbook)
    if step is None or step.status != 'failed' or step.risk != 'readonly':
        raise AIRunbookError('只能跳过失败的只读步骤')
    from django.utils import timezone
    step.status = 'skipped'
    step.finished_at = timezone.now()
    step.save(update_fields=['status', 'finished_at'])
    advance_runbook_position(runbook)
    return step


def cancel_runbook(runbook, actor):
    require_runbook_owner(runbook, actor)
    if runbook.status in ('completed', 'cancelled'):
        raise AIRunbookError('Runbook 已经结束')
    from django.utils import timezone
    runbook.steps.filter(
        position__gte=runbook.current_step,
        status__in=('pending', 'awaiting_confirmation', 'failed'),
    ).update(status='cancelled', confirmation_token_hash='', finished_at=timezone.now())
    runbook.status = 'cancelled'
    runbook.error = ''
    runbook.save(update_fields=['status', 'error', 'updated_at'])
    return runbook


def serialize_runbook_step(step):
    return {
        'id': step.id,
        'position': step.position,
        'title': step.title,
        'tool_call': step.tool_call,
        'risk': step.risk,
        'status': step.status,
        'output': step.output,
        'error': step.error,
        'confirmed_at': step.confirmed_at,
        'started_at': step.started_at,
        'finished_at': step.finished_at,
    }


def serialize_runbook(runbook):
    return {
        'id': runbook.id,
        'title': runbook.title,
        'status': runbook.status,
        'current_step': runbook.current_step,
        'created_at': runbook.created_at,
        'updated_at': runbook.updated_at,
        'error': runbook.error,
        'steps': [serialize_runbook_step(step) for step in runbook.steps.all()],
    }
