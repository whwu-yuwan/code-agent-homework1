"""
Agent 集成测试
使用 mock 测试 Agent 循环，不实际调用 API
"""

import pytest
import os
import sys
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent import CodeAgent
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from exceptions import ContextError, APIError


class TestCodeAgent:
    """CodeAgent 测试"""

    @patch("agent.ChatOpenAI")
    def test_simple_response(self, mock_openai):
        """测试简单文本回复（无工具调用）"""
        mock_llm = MagicMock()
        mock_openai.return_value = mock_llm

        mock_response = AIMessage(content="这是回复")
        mock_llm.invoke.return_value = mock_response
        mock_llm.bind_tools.return_value = mock_llm

        agent = CodeAgent()
        result = agent.chat("你好")

        assert result == "这是回复"
        assert agent.message_count == 3  # system + user + assistant

    @patch("agent.ChatOpenAI")
    def test_tool_call_loop(self, mock_openai):
        """测试工具调用循环 - 验证工具 .invoke() 被正确调用"""
        mock_llm = MagicMock()
        mock_openai.return_value = mock_llm

        # 第一次调用：返回工具调用
        tool_call_response = AIMessage(
            content="",
            tool_calls=[{
                "id": "call_1",
                "name": "read_file",
                "args": {"file_path": "test.py"}
            }]
        )

        # 第二次调用：返回文本
        text_response = AIMessage(content="文件内容解释")

        mock_llm.invoke.side_effect = [tool_call_response, text_response]
        mock_llm.bind_tools.return_value = mock_llm

        # 创建真实的 mock 工具
        mock_tool = MagicMock()
        mock_tool.name = "read_file"
        mock_tool.invoke.return_value = "file content here"

        agent = CodeAgent()
        agent.tool_map = {"read_file": mock_tool}

        result = agent.chat("解释 test.py")

        # 验证工具 .invoke() 被正确调用
        mock_tool.invoke.assert_called_once_with(
            {"file_path": "test.py"},
            config={"callbacks": []}
        )
        # 验证返回了 LLM 的最终回复
        assert result == "文件内容解释"

    @patch("agent.ChatOpenAI")
    def test_reset_clears_history(self, mock_openai):
        """测试重置对话历史"""
        mock_llm = MagicMock()
        mock_openai.return_value = mock_llm
        mock_llm.invoke.return_value = AIMessage(content="reply")
        mock_llm.bind_tools.return_value = mock_llm

        agent = CodeAgent()
        agent.chat("hello")
        assert agent.message_count == 3

        agent.reset()
        assert agent.message_count == 1  # 只有 system message

    @patch("agent.ChatOpenAI")
    def test_max_iterations_fallback(self, mock_openai):
        """测试工具轮次耗尽时的兜底行为（不崩溃）"""
        mock_llm = MagicMock()
        mock_openai.return_value = mock_llm

        # 总是返回工具调用，模拟无限循环
        tool_call_response = AIMessage(
            content="",
            tool_calls=[{
                "id": "call_1",
                "name": "read_file",
                "args": {"file_path": "test.py"}
            }]
        )
        fallback_response = AIMessage(content="兜底回复")

        # 前 10 次返回工具调用，最后一次（不带 tools）返回兜底
        mock_llm.invoke.side_effect = [tool_call_response] * 10 + [fallback_response]
        mock_llm.bind_tools.return_value = mock_llm

        mock_tool = MagicMock()
        mock_tool.name = "read_file"
        mock_tool.invoke.return_value = "content"

        agent = CodeAgent()
        agent.tool_map = {"read_file": mock_tool}

        # 应该不崩溃，返回兜底消息
        result = agent.chat("解释 test.py")
        assert result == "兜底回复"

    @patch("agent.ChatOpenAI")
    def test_input_too_long_raises_context_error(self, mock_openai):
        """测试输入过长时抛出 ContextError"""
        mock_llm = MagicMock()
        mock_openai.return_value = mock_llm
        mock_llm.bind_tools.return_value = mock_llm

        agent = CodeAgent()

        # 构造超长输入（超过 MAX_CONTEXT_TOKENS * MAX_INPUT_TOKEN_RATIO = 32000 tokens）
        # tiktoken cl100k_base: 1 个 token ≈ 4 个英文字符，用多样化文本避免压缩
        long_input = "请解释这段代码的逻辑 " * 20000  # ~60000 tokens

        with pytest.raises(ContextError, match="输入过长"):
            agent.chat(long_input)

    @patch("agent.ChatOpenAI")
    def test_context_trimming_removes_old_groups(self, mock_openai):
        """测试上下文裁剪删除旧消息组，保留当前问题"""
        import config

        mock_llm = MagicMock()
        mock_openai.return_value = mock_llm
        mock_llm.invoke.return_value = AIMessage(content="reply")
        mock_llm.bind_tools.return_value = mock_llm

        agent = CodeAgent()

        # 临时降低裁剪阈值以便测试
        old_threshold = config.TRIM_THRESHOLD_TOKENS
        config.TRIM_THRESHOLD_TOKENS = 100
        try:
            # 添加多轮对话
            for i in range(5):
                agent.chat(f"问题 {i}")

            # 裁剪后应保留 SystemMessage + 最后一组 Human/AI
            # 验证最后一条消息是 AI 回复
            assert isinstance(agent.messages[-1], AIMessage)
            # 验证仍有 SystemMessage
            from langchain_core.messages import SystemMessage
            assert isinstance(agent.messages[0], SystemMessage)
            # 验证最后一个问题的消息被保护
            has_recent_human = any(
                isinstance(m, HumanMessage) and "问题 4" in m.content
                for m in agent.messages
            )
            assert has_recent_human, "当前问题的 HumanMessage 应被保护"
            # 验证旧消息被裁剪删除
            has_old_human = any(
                isinstance(m, HumanMessage) and "问题 0" in m.content
                for m in agent.messages
            )
            assert not has_old_human, "旧消息 '问题 0' 应被裁剪删除"
        finally:
            config.TRIM_THRESHOLD_TOKENS = old_threshold

    @patch("agent.ChatOpenAI")
    def test_tool_error_becomes_tool_message(self, mock_openai):
        """测试工具错误被捕获并转为 ToolMessage（而非抛出异常）"""
        mock_llm = MagicMock()
        mock_openai.return_value = mock_llm

        # 第一次调用返回工具调用
        tool_call_response = AIMessage(
            content="",
            tool_calls=[{
                "id": "call_err",
                "name": "read_file",
                "args": {"file_path": "/nonexistent"}
            }]
        )
        # 第二次调用返回文本
        text_response = AIMessage(content="文件不存在的解释")

        mock_llm.invoke.side_effect = [tool_call_response, text_response]
        mock_llm.bind_tools.return_value = mock_llm

        # Mock 工具抛出 ToolError
        from exceptions import ToolError
        mock_tool = MagicMock()
        mock_tool.name = "read_file"
        mock_tool.invoke.side_effect = ToolError("文件不存在: /nonexistent")

        agent = CodeAgent()
        agent.tool_map = {"read_file": mock_tool}

        # 应该不崩溃，工具错误被转为 ToolMessage
        result = agent.chat("解释这个文件")
        assert result == "文件不存在的解释"

        # 验证 ToolMessage 包含错误信息
        tool_messages = [m for m in agent.messages if isinstance(m, ToolMessage)]
        assert len(tool_messages) == 1
        assert "[工具错误]" in tool_messages[0].content

    @patch("agent.ChatOpenAI")
    def test_token_stats_update(self, mock_openai):
        """测试 token 统计更新"""
        mock_llm = MagicMock()
        mock_openai.return_value = mock_llm

        # 模拟带 usage_metadata 的响应
        mock_response = AIMessage(content="reply")
        mock_response.usage_metadata = {"total_tokens": 150}
        mock_llm.invoke.return_value = mock_response
        mock_llm.bind_tools.return_value = mock_llm

        agent = CodeAgent()
        assert agent.total_tokens_used == 0

        agent.chat("hello")
        assert agent.total_tokens_used == 150

        agent.chat("world")
        assert agent.total_tokens_used == 300

    @patch("agent.ChatOpenAI")
    def test_api_failure_cleans_human_message(self, mock_openai):
        """测试 API 失败后 HumanMessage 被清理（不残留在历史中）"""
        mock_llm = MagicMock()
        mock_openai.return_value = mock_llm
        mock_llm.bind_tools.return_value = mock_llm

        # 第一次调用抛出异常
        mock_llm.invoke.side_effect = Exception("API 超时")

        agent = CodeAgent()
        initial_count = agent.message_count  # 1 (SystemMessage)

        with pytest.raises(APIError):
            agent.chat("这个问题会失败")

        # API 失败后，HumanMessage 应被清理，回到初始状态
        assert agent.message_count == initial_count
        assert not any(isinstance(m, HumanMessage) for m in agent.messages)

    @patch("agent.ChatOpenAI")
    def test_truncate_tool_result(self, mock_openai):
        """测试工具结果截断保留头部和尾部"""
        mock_llm = MagicMock()
        mock_openai.return_value = mock_llm
        mock_llm.bind_tools.return_value = mock_llm

        agent = CodeAgent()

        # 构造超长结果（超过 MAX_TOOL_RESULT_TOKENS = 4000 tokens）
        # 用多样化中文文本避免 tiktoken 高效压缩
        line = "这是一行代码内容，包含变量名和函数定义等信息。\n"
        head_content = "HEAD_START\n" + line * 3000  # 头部标记
        tail_content = line * 3000 + "TAIL_END\n"    # 尾部标记
        long_result = head_content + tail_content

        truncated = agent._truncate_tool_result(long_result)

        # 应该被截断
        assert len(truncated) < len(long_result)
        # 头部内容应保留
        assert "HEAD_START" in truncated
        # 尾部内容应保留
        assert "TAIL_END" in truncated
        # 截断提示应存在
        assert "截断" in truncated

    @patch("agent.ChatOpenAI")
    def test_empty_response_returns_placeholder(self, mock_openai):
        """测试 LLM 空回复时返回占位提示，且入历史的是 fallback 内容"""
        mock_llm = MagicMock()
        mock_openai.return_value = mock_llm
        mock_llm.bind_tools.return_value = mock_llm

        # 返回空内容
        mock_llm.invoke.return_value = AIMessage(content="")

        agent = CodeAgent()
        result = agent.chat("你好")

        assert "未生成有效回复" in result
        # 历史中最后一条应是 fallback 内容（不是空字符串）
        last_ai = agent.messages[-1]
        assert isinstance(last_ai, AIMessage)
        assert "未生成有效回复" in last_ai.content

    @patch("agent.ChatOpenAI")
    def test_api_failure_rollback_token_stats(self, mock_openai):
        """测试 API 失败时 token 统计被回滚"""
        mock_llm = MagicMock()
        mock_openai.return_value = mock_llm
        mock_llm.bind_tools.return_value = mock_llm

        agent = CodeAgent()
        agent.total_tokens_used = 500  # 模拟已有的 token 使用

        # 模拟 API 失败
        mock_llm.invoke.side_effect = Exception("API 超时")

        with pytest.raises(APIError):
            agent.chat("这个问题会失败")

        # token 统计应回滚到失败前
        assert agent.total_tokens_used == 500