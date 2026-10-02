"""
自定义异常模块
定义 Agent 相关的异常类层次结构
"""


class AgentError(Exception):
    """Agent 基础异常类

    所有 Agent 相关异常的父类
    """
    pass


class ToolError(AgentError):
    """工具执行异常

    当工具执行失败时抛出
    """
    pass


class APIError(AgentError):
    """API 调用异常

    当 LLM API 调用失败时抛出
    """
    pass


class ContextError(AgentError):
    """上下文异常

    当对话上下文出现问题时抛出（如 token 超限）
    """
    pass


class ConfigError(AgentError):
    """配置异常

    当配置出现问题时抛出（如 API Key 未设置）
    """
    pass


class InputError(AgentError):
    """输入异常

    当用户输入无效时抛出
    """
    pass