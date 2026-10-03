"""
Agent 核心模块
使用 LangChain 构建代码解释 Agent，管理 Agent 循环和工具调用
"""

import logging
from typing import List, Tuple, Optional, Union

import tiktoken
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage

import config
from tools import TOOLS
from prompts import SYSTEM_PROMPT
from callbacks import verbose_manager
from exceptions import ToolError, APIError, ContextError

logger = logging.getLogger(__name__)


class CodeAgent:
    """代码解释 Agent

    使用 LangChain 构建，支持：
    - 多轮对话上下文记忆
    - 上下文 token 裁剪（配对删除）
    - 工具调用（文件读取、目录浏览、代码执行、代码搜索）
    - 错误分类处理（ToolError、APIError、ContextError）
    - Verbose 模式（显示工具调用详情）
    - Token 使用统计
    """

    def __init__(self):
        """初始化 Agent"""
        self.llm = ChatOpenAI(
            model=config.MODEL_NAME,
            openai_api_key=config.API_KEY,
            openai_api_base=config.API_BASE_URL,
            temperature=config.TEMPERATURE,
            max_tokens=config.MAX_TOKENS,
            max_retries=2,
            timeout=30,
        )

        # 绑定工具到 LLM
        self.llm_with_tools = self.llm.bind_tools(TOOLS)

        # 工具映射，用于执行工具调用
        self.tool_map = {tool.name: tool for tool in TOOLS}

        # 对话历史
        self.messages: List[Union[SystemMessage, HumanMessage, AIMessage, ToolMessage]] = [
            SystemMessage(content=SYSTEM_PROMPT)
        ]

        # Token 使用统计
        self.total_tokens_used = 0

        # tiktoken 编码器（用于上下文裁剪）
        self._encoding = tiktoken.get_encoding("cl100k_base")

        logger.info("CodeAgent 初始化完成")

    def _estimate_tokens(self) -> int:
        """估算当前对话历史的 token 数量"""
        total = 0
        for msg in self.messages:
            content = msg.content if msg.content else ""
            total += len(self._encoding.encode(content))
            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                for tc in msg.tool_calls:
                    total += len(self._encoding.encode(str(tc)))
        return total

    def _estimate_msg_tokens(self, msg) -> int:
        """估算单条消息的 token 数量"""
        tokens = len(self._encoding.encode(msg.content or ""))
        if hasattr(msg, 'tool_calls') and msg.tool_calls:
            for tc in msg.tool_calls:
                tokens += len(self._encoding.encode(str(tc)))
        return tokens

    def _find_removable_group(self, protect_start: int = 0) -> Optional[Tuple[int, int]]:
        """找到第一个可安全删除的消息组。

        消息组 = HumanMessage + 对应的 AIMessage（含 tool_calls 和 ToolMessage）
        删除时保证不拆散 Human/AI 对。

        Args:
            protect_start: 保护起点索引，该索引及之后的消息组不会被删除（保护当前问题）

        Returns:
            (start, end) 可删除的索引范围 [start, end)，或 None
        """
        idx = 1  # 跳过 system message
        while idx < len(self.messages):
            msg = self.messages[idx]
            if isinstance(msg, HumanMessage):
                # 找到一个 HumanMessage，它到下一个 HumanMessage（或末尾）构成一个组
                start = idx
                end = idx + 1
                while end < len(self.messages) and not isinstance(self.messages[end], HumanMessage):
                    end += 1
                # 保护当前问题组：如果该组与保护范围重叠，则跳过
                if start >= protect_start:
                    return None
                return (start, end)
            elif isinstance(msg, (ToolMessage, AIMessage)):
                # 孤立的 ToolMessage 或 AIMessage（前面没有 HumanMessage），可以删除
                start = idx
                end = idx + 1
                while end < len(self.messages) and isinstance(self.messages[end], (ToolMessage, AIMessage)):
                    end += 1
                if start >= protect_start:
                    return None
                return (start, end)
            else:
                idx += 1
        return None

    def _remove_group(self, start: int, end: int) -> int:
        """删除消息组并返回释放的 token 数。

        Args:
            start: 起始索引（包含）
            end: 结束索引（不包含）

        Returns:
            释放的 token 数量
        """
        freed = 0
        for i in range(end - 1, start - 1, -1):
            freed += self._estimate_msg_tokens(self.messages[i])
            self.messages.pop(i)
        return freed

    def _trim_context(self) -> None:
        """裁剪对话历史，确保不超过 token 限制。

        策略：从最旧的消息组开始整体删除，保持 Human/AI 对不被拆散。
        保护当前问题组（最后一条 HumanMessage 及其后续消息）不被删除。
        """
        current_tokens = self._estimate_tokens()

        if current_tokens <= config.TRIM_THRESHOLD_TOKENS:
            return

        logger.info(f"上下文裁剪: 当前 {current_tokens} tokens，阈值 {config.TRIM_THRESHOLD_TOKENS}")

        while current_tokens > config.TRIM_THRESHOLD_TOKENS and len(self.messages) > config.MIN_MESSAGES_TO_KEEP:
            # 每次裁剪前重新计算保护起点（最后一条 HumanMessage 的位置）
            protect_start = 0
            for i in range(len(self.messages) - 1, 0, -1):
                if isinstance(self.messages[i], HumanMessage):
                    protect_start = i
                    break

            group = self._find_removable_group(protect_start=protect_start)
            if group is None:
                break
            start, end = group
            freed = self._remove_group(start, end)
            current_tokens -= freed

        logger.info(f"上下文裁剪完成: 剩余 {len(self.messages)} 条消息，约 {current_tokens} tokens")

    def _force_final_response(self, callbacks: list) -> str:
        """强制生成最终回复（不带 tools）。

        在工具调用轮次耗尽或最后一轮仍有工具调用时调用。

        Args:
            callbacks: 回调处理器列表

        Returns:
            Agent 的回复文本
        """
        response = self.llm.invoke(self.messages, config={"callbacks": callbacks})
        self._update_token_stats(response)
        # 检查空回复
        if not response.content or not response.content.strip():
            fallback = "（Agent 未生成有效回复，请重试）"
            self.messages.append(AIMessage(content=fallback))
            return fallback
        self.messages.append(response)
        return response.content

    def _update_token_stats(self, response: AIMessage) -> None:
        """更新 token 使用统计"""
        if hasattr(response, 'usage_metadata') and response.usage_metadata:
            tokens = response.usage_metadata.get('total_tokens', 0)
            self.total_tokens_used += tokens

    def _truncate_tool_result(self, result: str) -> str:
        """截断过长的工具结果，防止撑爆上下文。

        保留头部 70% 和尾部 30%，中间插入截断提示。
        对于代码文件，头部通常是 import/定义，尾部通常是 main 入口或最后的函数。

        Args:
            result: 工具返回的原始结果

        Returns:
            截断后的结果（如未超限则原样返回）
        """
        tokens = len(self._encoding.encode(result))
        if tokens <= config.MAX_TOOL_RESULT_TOKENS:
            return result

        # 按比例计算保留字符数，留 10% 余量给截断提示
        keep_ratio = config.MAX_TOOL_RESULT_TOKENS / tokens
        keep_chars = int(len(result) * keep_ratio * 0.9)
        # 头部 70%，尾部 30%
        head_chars = int(keep_chars * 0.7)
        tail_chars = keep_chars - head_chars

        truncation_notice = f"\n\n... [结果过长，已截断（原始约 {tokens} tokens，保留约 {config.MAX_TOOL_RESULT_TOKENS} tokens）] ...\n\n"
        truncated = result[:head_chars] + truncation_notice + result[-tail_chars:]
        logger.info(f"工具结果截断: {tokens} → ~{config.MAX_TOOL_RESULT_TOKENS} tokens")
        return truncated

    def _execute_tool_calls(self, tool_calls: list, callbacks: list) -> None:
        """执行工具调用并将结果追加到 messages。

        Args:
            tool_calls: LLM 返回的 tool_calls 列表
            callbacks: 回调处理器列表
        """
        for tool_call in tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            tool_id = tool_call["id"]

            try:
                tool_func = self.tool_map.get(tool_name)
                if not tool_func:
                    raise ToolError(f"未知工具: {tool_name}")
                result = tool_func.invoke(
                    tool_args,
                    config={"callbacks": callbacks}
                )
            except ToolError as e:
                result = f"[工具错误] {e}"
            except Exception as e:
                logger.error(f"工具 '{tool_name}' 意外异常: {e}")
                result = f"[工具执行异常] {tool_name}: {e}"

            # 截断过长的工具结果
            result_str = self._truncate_tool_result(str(result))

            self.messages.append(
                ToolMessage(content=result_str, tool_call_id=tool_id)
            )

    def chat(self, user_input: str) -> str:
        """处理用户输入，执行 Agent 循环。

        Args:
            user_input: 用户输入的文本

        Returns:
            Agent 的回复文本

        Raises:
            ContextError: 输入过长
            APIError: LLM 调用失败
            AgentError: 其他 Agent 错误
        """
        # 输入长度前置校验
        input_tokens = len(self._encoding.encode(user_input))
        if input_tokens > config.MAX_CONTEXT_TOKENS * config.MAX_INPUT_TOKEN_RATIO:
            raise ContextError(f"输入过长（约 {input_tokens} tokens），请缩短输入后重试。")

        # 记录添加用户消息前的快照（API 失败时回滚到此处，清理 HumanMessage）
        pre_input_len = len(self.messages)

        # 添加用户消息到历史
        self.messages.append(HumanMessage(content=user_input))
        logger.info(f"用户输入: {user_input[:100]}...")

        # 裁剪上下文
        self._trim_context()

        # 获取回调处理器
        callbacks = [verbose_manager.handler] if verbose_manager.verbose else []

        # 记录消息快照，用于最终兜底失败时回滚
        snapshot_len = len(self.messages)

        # Agent 循环（最多 MAX_TOOL_CALLS_PER_TURN 次工具调用）
        max_iters = config.MAX_TOOL_CALLS_PER_TURN
        last_iteration_had_tools = False

        for iteration in range(max_iters):
            try:
                # 调用 LLM（带回调）
                response = self.llm_with_tools.invoke(
                    self.messages,
                    config={"callbacks": callbacks}
                )

                # 统计 token
                self._update_token_stats(response)

                # 检查是否有工具调用
                if response.tool_calls:
                    # 添加 AI 消息（包含工具调用）到历史
                    self.messages.append(response)

                    # 执行工具调用
                    self._execute_tool_calls(response.tool_calls, callbacks)
                    last_iteration_had_tools = True

                    # 最后一次迭代：工具结果已追加，跳出循环进入统一兜底
                    if iteration == max_iters - 1:
                        logger.warning("最后一次迭代仍有工具调用，进入强制回复")
                        break

                    continue
                else:
                    # 没有工具调用，返回文本回复
                    self.messages.append(response)
                    logger.info(f"Agent 回复完成 (迭代 {iteration + 1})")
                    # 检查空回复
                    if not response.content or not response.content.strip():
                        return "（Agent 未生成有效回复，请重试）"
                    return response.content

            except Exception as e:
                # 执行失败：回滚到添加用户消息之前，清理残留的 HumanMessage
                del self.messages[pre_input_len:]
                logger.error(f"Agent 执行出错 (迭代 {iteration + 1}): {e}")
                raise APIError(f"Agent 执行失败: {e}")

        # 工具调用轮次耗尽或最后一轮仍有工具调用：强制生成文本回复
        logger.warning(f"工具调用轮次耗尽 ({max_iters})，尝试强制生成回复")
        try:
            return self._force_final_response(callbacks)
        except Exception:
            # 兜底失败：回滚到本轮开始前，保留用户消息
            del self.messages[snapshot_len:]
            fallback = "抱歉，处理过程过于复杂，请简化问题后重试。"
            self.messages.append(AIMessage(content=fallback))
            return fallback

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