"""
配置常量模块
包含 API 地址、模型名称、重试策略、日志配置等
"""

import os

# DeepSeek API 配置
API_BASE_URL = "https://api.deepseek.com"
API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
MODEL_NAME = "deepseek-chat"

# 上下文管理
MAX_CONTEXT_TOKENS = 64000
TRIM_THRESHOLD_TOKENS = 50000

# 工具配置
MAX_TOOL_CALLS_PER_TURN = 10
MAX_FILE_READ_BYTES = 1_000_000  # 1MB
CODE_EXECUTION_TIMEOUT = 10  # 秒
MAX_SEARCH_RESULTS = 50  # 搜索结果最大数量

# 重试配置
RETRY_MAX_ATTEMPTS = 3
RETRY_BASE_DELAY = 1.0
RETRY_MAX_DELAY = 30.0
RETRY_BACKOFF_FACTOR = 2

# 日志配置
LOG_FILE = "logs/agent.log"
LOG_CONSOLE_LEVEL = 20  # INFO
LOG_FILE_LEVEL = 10  # DEBUG

# Token 编码
TOKEN_ENCODING_NAME = "cl100k_base"