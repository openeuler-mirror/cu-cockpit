import json

from .ai_tools import tool_catalog


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
    return json.loads(content)
