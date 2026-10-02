"""
Agent 核心模块
使用 LangChain 构建代码解释 Agent，管理 Agent 循环和工具调用
"""

import logging
from typing import List, Optional

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

import config
from tools import TOOLS
from prompts import SYSTEM_PROMPT
from callbacks import verbose_manager
from exceptions import AgentError, ToolError, APIError

# 创建日志记录器
logger = logging.getLogger(__name__)


class CodeAgent:
    """代码解释 Agent

    使用 LangChain 构建，支持：
    - 多轮对话上下文记忆
    - 工具调用（文件读取、目录浏览、代码执行、代码搜索、注释生成）
    - 错误处理和重试
    - Verbose 模式（显示工具调用详情）
    - Token 使用统计
    """

    def __init__(self):
        """初始化 Agent"""
        # 创建 LLM 实例（DeepSeek API，兼容 OpenAI 接口）
        self.llm = ChatOpenAI(
            model=config.MODEL_NAME,
            openai_api_key=config.API_KEY,
            openai_api_base=config.API_BASE_URL,
            temperature=0.3,
            max_tokens=4096,
        )

        # 绑定工具到 LLM
        self.llm_with_tools = self.llm.bind_tools(TOOLS)

        # 工具映射，用于执行工具调用
        self.tool_map = {tool.name: tool for tool in TOOLS}

        # 对话历史
        self.messages: List[SystemMessage | HumanMessage | AIMessage | ToolMessage] = [
            SystemMessage(content=SYSTEM_PROMPT)
        ]

        # Token 使用统计
        self.total_tokens_used = 0

        logger.info("CodeAgent 初始化完成")

    def chat(self, user_input: str) -> str:
        """处理用户输入，执行 Agent 循环

        Agent 循环：
        1. 用户输入 → 添加到对话历史
        2. 调用 LLM（带工具定义）
        3. 如果 LLM 返回工具调用 → 执行工具 → 结果加入历史 → 回到步骤 2
        4. 如果 LLM 返回文本 → 输出给用户

        Args:
            user_input: 用户输入的文本

        Returns:
            Agent 的回复文本

        Raises:
            AgentError: Agent 循环出错时抛出
        """
        # 添加用户消息到历史
        self.messages.append(HumanMessage(content=user_input))
        logger.info(f"用户输入: {user_input[:100]}...")

        # 获取回调处理器
        callbacks = [verbose_manager.handler] if verbose_manager.verbose else []

        # Agent 循环（最多 MAX_TOOL_CALLS_PER_TURN 次工具调用）
        for iteration in range(config.MAX_TOOL_CALLS_PER_TURN):
            try:
                # 调用 LLM（带回调）
                response = self.llm_with_tools.invoke(
                    self.messages,
                    config={"callbacks": callbacks}
                )

                # 检查是否有工具调用
                if response.tool_calls:
                    # 添加 AI 消息（包含工具调用）到历史
                    self.messages.append(response)

                    # 执行每个工具调用
                    for tool_call in response.tool_calls:
                        tool_name = tool_call["name"]
                        tool_args = tool_call["args"]
                        tool_id = tool_call["id"]

                        # 执行工具
                        try:
                            tool_func = self.tool_map.get(tool_name)
                            if tool_func:
                                result = tool_func.invoke(tool_args)
                            else:
                                result = f"[错误] 未知工具: {tool_name}"
                        except Exception as e:
                            result = f"[错误] 工具执行失败: {e}"
                            logger.error(f"工具执行失败: {tool_name} - {e}")

                        # 添加工具结果到历史
                        self.messages.append(
                            ToolMessage(content=str(result), tool_call_id=tool_id)
                        )

                    # 继续循环，让 LLM 处理工具结果
                    continue

                else:
                    # 没有工具调用，返回文本回复
                    self.messages.append(response)

                    # 统计 token 使用
                    if hasattr(response, 'usage_metadata') and response.usage_metadata:
                        tokens = response.usage_metadata.get('total_tokens', 0)
                        self.total_tokens_used += tokens

                    logger.info(f"Agent 回复完成 (迭代 {iteration + 1})")
                    return response.content

            except Exception as e:
                logger.error(f"Agent 执行出错: {e}")
                raise AgentError(f"Agent 执行出错: {e}")

        # 超过最大工具调用次数
        logger.warning(f"超过最大工具调用次数 ({config.MAX_TOOL_CALLS_PER_TURN})")
        raise AgentError(f"超过最大工具调用次数 ({config.MAX_TOOL_CALLS_PER_TURN})")

    def reset(self):
        """重置对话历史"""
        self.messages = [SystemMessage(content=SYSTEM_PROMPT)]
        self.total_tokens_used = 0
        verbose_manager.reset()
        logger.info("对话历史已重置")

    @property
    def message_count(self) -> int:
        """获取对话历史中的消息数量"""
        return len(self.messages)

    def get_conversation_summary(self) -> str:
        """获取对话摘要"""
        user_msgs = sum(1 for m in self.messages if isinstance(m, HumanMessage))
        ai_msgs = sum(1 for m in self.messages if isinstance(m, AIMessage))
        tool_calls = sum(1 for m in self.messages if isinstance(m, ToolMessage))

        summary = f"📊 对话统计:\n"
        summary += f"  - 用户消息: {user_msgs}\n"
        summary += f"  - AI 回复: {ai_msgs}\n"
        summary += f"  - 工具调用: {tool_calls}\n"
        summary += f"  - 总消息数: {len(self.messages)}\n"
        summary += f"  - Token 使用: {self.total_tokens_used}"

        return summary