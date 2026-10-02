"""
Agent 核心模块
使用 LangChain 构建代码解释 Agent，管理 Agent 循环和工具调用
"""

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

import config
from tools import TOOLS
from prompts import SYSTEM_PROMPT


class CodeAgent:
    """代码解释 Agent

    使用 LangChain 构建，支持：
    - 多轮对话上下文记忆
    - 工具调用（文件读取、目录浏览、代码执行）
    - 错误处理和重试
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
        self.messages = [SystemMessage(content=SYSTEM_PROMPT)]

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

        # Agent 循环（最多 MAX_TOOL_CALLS_PER_TURN 次工具调用）
        for _ in range(config.MAX_TOOL_CALLS_PER_TURN):
            try:
                # 调用 LLM
                response = self.llm_with_tools.invoke(self.messages)

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

                        # 添加工具结果到历史
                        self.messages.append(
                            ToolMessage(content=str(result), tool_call_id=tool_id)
                        )

                    # 继续循环，让 LLM 处理工具结果
                    continue

                else:
                    # 没有工具调用，返回文本回复
                    self.messages.append(response)
                    return response.content

            except Exception as e:
                raise AgentError(f"Agent 执行出错: {e}")

        # 超过最大工具调用次数
        raise AgentError(f"超过最大工具调用次数 ({config.MAX_TOOL_CALLS_PER_TURN})")

    def reset(self):
        """重置对话历史"""
        self.messages = [SystemMessage(content=SYSTEM_PROMPT)]

    @property
    def message_count(self) -> int:
        """获取对话历史中的消息数量"""
        return len(self.messages)


class AgentError(Exception):
    """Agent 相关错误"""
    pass