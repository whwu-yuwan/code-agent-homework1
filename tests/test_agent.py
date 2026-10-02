"""
Agent 集成测试
使用 mock 测试 Agent 循环，不实际调用 API
"""

import pytest
import os
import sys
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent import CodeAgent, AgentError
from langchain_core.messages import AIMessage, ToolMessage


class TestCodeAgent:
    """CodeAgent 测试"""

    @patch("agent.ChatOpenAI")
    def test_simple_response(self, mock_openai):
        """测试简单文本回复（无工具调用）"""
        # Mock LLM 返回文本
        mock_llm = MagicMock()
        mock_openai.return_value = mock_llm

        # 创建 mock 响应
        mock_response = AIMessage(content="这是回复")
        mock_llm.invoke.return_value = mock_response
        mock_llm.bind_tools.return_value = mock_llm

        agent = CodeAgent()
        result = agent.chat("你好")

        assert result == "这是回复"
        assert agent.message_count == 3  # system + user + assistant

    @patch("agent.ChatOpenAI")
    def test_tool_call_loop(self, mock_openai):
        """测试工具调用循环"""
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

        # Mock 工具执行
        with patch("agent.TOOLS", []):
            agent = CodeAgent()
            # 需要手动 mock tool_map
            agent.tool_map = {"read_file": MagicMock(return_value="file content")}
            result = agent.chat("解释 test.py")

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