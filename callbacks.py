"""
LangChain 回调模块
实现自定义回调处理器，用于显示工具调用详情和 Agent 思考过程
"""

import time
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult

import config

# 创建日志记录器
logger = logging.getLogger(__name__)


class ToolCallbackHandler(BaseCallbackHandler):
    """工具调用回调处理器

    记录和显示工具调用的详情，包括：
    - 工具名称和参数
    - 执行时间
    - 执行结果摘要
    """

    def __init__(self, verbose: bool = True):
        """初始化回调处理器

        Args:
            verbose: 是否显示详细信息
        """
        super().__init__()
        self.verbose = verbose
        self.tool_calls_log: List[Dict[str, Any]] = []
        self._tool_start_times: Dict[str, float] = {}
        self._tool_names: Dict[str, str] = {}  # run_id -> tool_name 映射

    def on_tool_start(
        self,
        serialized: Dict[str, Any],
        input_str: str,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        inputs: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """工具开始执行时调用"""
        tool_name = serialized.get("name", "unknown")
        run_id_str = str(run_id)

        # 存储 run_id -> tool_name 映射
        self._tool_names[run_id_str] = tool_name
        self._tool_start_times[run_id_str] = time.time()

        if self.verbose:
            print(f"\n  🔧 调用工具: {tool_name}")
            if inputs:
                # 显示参数（截断过长的参数）
                args_str = str(inputs)
                if len(args_str) > config.ARGS_PREVIEW_LENGTH:
                    args_str = args_str[:config.ARGS_PREVIEW_LENGTH] + "..."
                print(f"     参数: {args_str}")

        logger.info(f"Tool started: {tool_name}")

    def on_tool_end(
        self,
        output: str,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        """工具执行完成时调用"""
        run_id_str = str(run_id)

        # 从映射中获取真实工具名
        tool_name = self._tool_names.pop(run_id_str, "unknown")
        elapsed = 0.0

        # 计算执行时间
        if run_id_str in self._tool_start_times:
            elapsed = time.time() - self._tool_start_times.pop(run_id_str)

        # 确保 output 为字符串（工具可能返回非 str 类型）
        output_str = str(output) if not isinstance(output, str) else output

        if self.verbose:
            # 显示结果摘要
            result_preview = output_str[:config.ARGS_PREVIEW_LENGTH] + "..." if len(output_str) > config.ARGS_PREVIEW_LENGTH else output_str
            print(f"     ✅ 完成 ({elapsed:.2f}s)")
            if output_str and output_str != "(无输出)":
                print(f"     结果: {result_preview}")

        # 记录日志
        self.tool_calls_log.append({
            "tool": tool_name,
            "output_preview": output_str[:100] if output_str else "",
            "elapsed": elapsed,
        })

        logger.info(f"Tool completed: {tool_name} ({elapsed:.2f}s)")

    def on_tool_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        """工具执行出错时调用"""
        run_id_str = str(run_id)
        tool_name = self._tool_names.pop(run_id_str, "unknown")

        if self.verbose:
            print(f"     ❌ 错误: {error}")

        logger.error(f"Tool error ({tool_name}): {error}")

    def on_llm_start(
        self,
        serialized: Dict[str, Any],
        prompts: List[str],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        """LLM 开始调用时"""
        if self.verbose:
            print("\n  🧠 思考中...")

    def on_llm_end(
        self,
        response: LLMResult,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        """LLM 调用完成时"""
        if self.verbose and response.llm_output:
            token_usage = response.llm_output.get("token_usage", {})
            if token_usage:
                total_tokens = token_usage.get("total_tokens", 0)
                print(f"     📊 Token 使用: {total_tokens}")

    def get_summary(self) -> Dict[str, Any]:
        """获取工具调用摘要"""
        return {
            "total_calls": len(self.tool_calls_log),
            "calls": self.tool_calls_log,
            "total_time": sum(c["elapsed"] for c in self.tool_calls_log),
        }

    def reset(self):
        """重置日志"""
        self.tool_calls_log.clear()
        self._tool_start_times.clear()
        self._tool_names.clear()


class VerboseManager:
    """Verbose 模式管理器

    管理 verbose 状态和回调处理器的生命周期
    """

    def __init__(self):
        self._verbose = False
        self._handler = ToolCallbackHandler(verbose=False)

    @property
    def verbose(self) -> bool:
        return self._verbose

    @verbose.setter
    def verbose(self, value: bool):
        self._verbose = value
        self._handler.verbose = value

    @property
    def handler(self) -> ToolCallbackHandler:
        return self._handler

    def toggle(self) -> bool:
        """切换 verbose 模式"""
        self.verbose = not self.verbose
        return self.verbose

    def get_summary(self) -> Dict[str, Any]:
        """获取工具调用摘要"""
        return self._handler.get_summary()

    def reset(self):
        """重置"""
        self._handler.reset()


# 全局 Verbose 管理器实例
verbose_manager = VerboseManager()