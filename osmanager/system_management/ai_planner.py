import json

from .ai_context import redact_context
from .ai_provider import chat_completion
from .ai_tools import AIToolValidationError, normalize_tool_call, tool_catalog


class AIPlanValidationError(ValueError):
    pass


def build_plan_messages(request_text):
    catalog = json.dumps(tool_catalog(), ensure_ascii=False)
    system = (
        '你是 cu-cockpit 受控运维规划器。只能从给定工具目录选择一个工具，'
        '不得生成或建议执行原始 Shell、管道、重定向或命令替换。'
        '只返回 JSON 对象，格式为 '
        '{"intent":"意图","summary":"影响说明","tool_calls":'
        '[{"tool":"注册工具名","arguments":{}}]}。工具目录：' + catalog
    )
    return [
        {'role': 'system', 'content': system},
        {'role': 'user', 'content': str(request_text)},
    ]


def parse_plan_response(content):
    try:
        return json.loads(content)
    except (json.JSONDecodeError, TypeError) as error:
        raise AIPlanValidationError('AI 计划不是有效 JSON') from error


def validate_plan_payload(payload):
    if not isinstance(payload, dict) or not isinstance(payload.get('tool_calls'), list):
        raise AIPlanValidationError('AI 计划必须为对象且 tool_calls 必须为数组')
    unknown = sorted(set(payload) - {'intent', 'summary', 'tool_calls'})
    if unknown:
        raise AIPlanValidationError(f'AI 计划包含未知字段: {", ".join(unknown)}')
    if len(payload['tool_calls']) != 1:
        raise AIPlanValidationError('单次 AI 计划必须且只能包含一个工具调用')
    intent = str(payload.get('intent') or '').strip()
    summary = str(payload.get('summary') or '').strip()
    if not intent or len(intent) > 256 or len(summary) > 2000:
        raise AIPlanValidationError('AI 计划意图或摘要长度无效')
    try:
        spec, arguments = normalize_tool_call(payload['tool_calls'][0])
    except AIToolValidationError as error:
        raise AIPlanValidationError(str(error)) from error
    return {
        'intent': intent,
        'summary': summary,
        'risk': spec.risk,
        'tool_calls': [{'tool': spec.name, 'arguments': arguments}],
    }


def generate_plan(request_text):
    text = str(request_text or '').strip()
    if not text or len(text) > 2000:
        raise AIPlanValidationError('运维请求不能为空且不能超过 2000 字符')
    content = chat_completion(build_plan_messages(text))
    return validate_plan_payload(parse_plan_response(content))


def create_operation_plan(request_text, actor):
    from .models import AIOperationPlan
    payload = generate_plan(request_text)
    return AIOperationPlan.objects.create(
        actor=actor,
        request_text=redact_context(str(request_text).strip()),
        intent=payload['intent'],
        summary=payload['summary'],
        risk=payload['risk'],
        tool_calls=payload['tool_calls'],
    )


def serialize_operation_plan(plan):
    return {
        'id': plan.id,
        'intent': plan.intent,
        'summary': plan.summary,
        'risk': plan.risk,
        'tool_calls': plan.tool_calls,
        'status': plan.status,
        'created_at': plan.created_at,
        'executed_at': plan.executed_at,
        'result': plan.result,
        'error': plan.error,
    }
