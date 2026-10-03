"""
配置常量模块
包含 API 地址、模型名称、工具配置、日志配置等
"""

import os

# DeepSeek API 配置
API_BASE_URL = "https://api.deepseek.com"
API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
MODEL_NAME = "deepseek-chat"

# LLM 参数
TEMPERATURE = 0.3
MAX_TOKENS = 4096

# 上下文管理
MAX_CONTEXT_TOKENS = 64000
MAX_OUTPUT_TOKENS = 4096           # LLM 最大输出 token
TOOL_RESULT_RESERVE_TOKENS = 8000  # 工具结果预留 token 预算
# 裁剪阈值 = 窗口 - 输出 - 工具预留，确保留有余量
TRIM_THRESHOLD_TOKENS = MAX_CONTEXT_TOKENS - MAX_OUTPUT_TOKENS - TOOL_RESULT_RESERVE_TOKENS

# 工具配置
MAX_TOOL_CALLS_PER_TURN = 10
MAX_FILE_READ_BYTES = 200_000     # 200KB（与 token 窗口匹配，避免单文件撑爆上下文）
MAX_TOOL_RESULT_TOKENS = 4000     # 单个工具结果的 token 上限，超出则截断
MAX_SEARCH_RESULTS = 50           # search_code 最大结果数
CODE_EXECUTION_TIMEOUT = 10       # 秒

# 截断策略
TRUNCATE_HEAD_RATIO = 0.7         # 截断时头部保留比例（尾部 1 - ratio）
ARGS_PREVIEW_LENGTH = 200         # callbacks 中参数预览最大字符数

# 输入校验
MAX_INPUT_TOKEN_RATIO = 0.5       # 输入 token 占最大上下文的比例上限

# 消息保护
MIN_MESSAGES_TO_KEEP = 2          # 裁剪时最少保留的消息数（System + 当前 Human）

# 安全：工具文件操作限制在当前工作目录下（延迟求值，不在 import 时固化）
# None → 首次使用时 fallback 到 os.getcwd()
# "/" → 允许所有路径（测试用）
ALLOWED_PATH_PREFIX = None

# 日志配置
LOG_FILE = "logs/agent.log"
LOG_CONSOLE_LEVEL = 30  # WARNING（避免 INFO 日志污染 CLI 界面）
LOG_FILE_LEVEL = 10  # DEBUG