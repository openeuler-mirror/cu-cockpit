ANALYSIS_PROMPTS = {
    'logs': '分析系统日志，返回摘要、关键证据、可能原因和按优先级排序的排查步骤。',
    'command_output': '解释 Linux 命令输出，返回结论、关键字段、异常点和下一步检查建议。',
    'config_diff': '审查配置差异，返回变更摘要、风险、验证步骤和回滚建议，不得直接修改配置。',
    'alert_context': '分析告警上下文，返回时间线、异常证据、可能原因和受控排查步骤。',
}


class AIAnalysisError(ValueError):
    pass
