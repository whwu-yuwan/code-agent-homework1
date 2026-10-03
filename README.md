# 🤖 代码解释 Agent (Code Explanation Agent)

一个基于 LangChain 和 DeepSeek API 的代码解释助手 Agent，能够读取代码文件、解释代码逻辑、生成注释、回答代码相关问题。

## ✨ 功能特性

### 核心功能
- **代码读取**：自动读取本地代码文件内容
- **代码解释**：理解代码逻辑，用清晰的中文解释
- **目录浏览**：查看项目结构，了解文件组织
- **代码执行**：运行 Python 代码片段，验证逻辑
- **代码搜索**：递归搜索代码中的关键词或正则表达式
- **错误分类**：工具错误、API 错误、输入错误分类处理

### 高级功能
- **多轮对话**：支持上下文记忆，连续提问
- **上下文裁剪**：token 超限时自动裁剪旧消息，防止上下文溢出
- **Verbose 模式**：显示工具调用详情和 Agent 思考过程
- **对话历史**：查看对话摘要和统计信息
- **对话保存**：导出对话记录到文件
- **日志系统**：完整的日志记录和错误追踪
- **错误处理**：工具错误、API 错误、输入错误分类处理，工具轮次耗尽不崩溃
- **安全限制**：文件操作限制在工作目录下，代码执行有超时限制

## 🛠️ 技术栈

- **Python 3.10+**
- **LangChain**：Agent 框架（Agent 执行、工具绑定、回调系统）
- **LangChain OpenAI**：连接 DeepSeek API（OpenAI 兼容接口）
- **tiktoken**：上下文 token 估算和裁剪
- **DeepSeek API**：大语言模型

## 📦 安装与运行

### 1. 克隆/下载项目

```bash
cd code-agent-homework1
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 设置 API Key

```bash
# Windows
set DEEPSEEK_API_KEY=your-api-key-here

# Linux/Mac
export DEEPSEEK_API_KEY=your-api-key-here
```

### 4. 运行 Agent

```bash
python main.py
```

## 📖 使用示例

> 以下为示意输出，实际运行结果取决于具体代码内容和 LLM 响应。

### 示例 1：解释代码文件

```
🧑 You > 请解释 main.py 的代码逻辑

🤖 Agent:
## 概述
main.py 是程序的入口文件，实现了命令行交互界面。

## 核心逻辑
1. `check_api_key()` - 检查 API Key 是否设置
2. `handle_command()` - 处理斜杠命令
3. `main()` - 主循环，处理用户输入
```

### 示例 2：Verbose 模式下查看工具调用

```
🧑 You > /verbose
✅ 详细模式已开启

🧑 You > 解释 tools.py

  🧠 思考中...

  🔧 调用工具: read_file
     参数: {'file_path': 'tools.py'}
     ✅ 完成 (0.01s)
     结果: """自定义工具模块...

  🧠 思考中...

🤖 Agent:
## 概述
tools.py 定义了 4 个工具...
```

### 示例 3：搜索代码

```
🧑 You > 搜索代码中所有使用 logging 的地方

🤖 Agent:
共找到 N 处匹配:
agent.py:19: logger = logging.getLogger(__name__)
main.py:7: import logging
...
（注：N 为实际匹配数量，取决于项目中的代码）
```

## 🎯 命令说明

| 命令 | 说明 |
|------|------|
| `/help` | 显示帮助信息 |
| `/reset` | 重置对话历史（清除上下文） |
| `/verbose` | 切换详细模式（显示工具调用详情） |
| `/history` | 查看对话历史摘要和统计信息 |
| `/save` | 保存对话记录到文件 |
| `/quit` | 退出程序 |

## 📁 项目结构

```
code-agent-homework1/
├── main.py              # 入口，CLI 交互界面
├── agent.py             # Agent 核心（循环、上下文裁剪、异常处理）
├── tools.py             # 4 个工具（读文件、列目录、执行代码、搜索）
├── prompts.py           # 系统提示词
├── config.py            # 配置常量
├── callbacks.py         # LangChain 回调处理器（Verbose 模式）
├── logger.py            # 日志配置模块
├── exceptions.py        # 自定义异常类层次结构
├── requirements.txt     # 依赖
├── README.md            # 项目文档
├── Design.md            # 设计文档
└── tests/               # 测试
    ├── conftest.py      # 测试配置
    ├── test_tools.py    # 工具测试（14 个）
    └── test_agent.py    # Agent 测试（9 个）
```

## 🧪 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试
pytest tests/test_tools.py -v
pytest tests/test_agent.py -v
```

## 🔧 配置说明

在 `config.py` 中可以修改以下配置：

```python
# DeepSeek API 配置
API_BASE_URL = "https://api.deepseek.com"
MODEL_NAME = "deepseek-chat"
TEMPERATURE = 0.3               # LLM 温度
MAX_TOKENS = 4096               # 最大输出 token

# 上下文管理
MAX_CONTEXT_TOKENS = 64000      # 最大上下文 token
MAX_OUTPUT_TOKENS = 4096        # LLM 最大输出 token
TOOL_RESULT_RESERVE_TOKENS = 8000  # 工具结果预留 token 预算
TRIM_THRESHOLD_TOKENS = 51904   # 裁剪阈值（自动计算）

# 输入校验
MAX_INPUT_TOKEN_RATIO = 0.5     # 输入 token 占最大上下文的比例上限

# 消息保护
MIN_MESSAGES_TO_KEEP = 2        # 裁剪时最少保留的消息数

# 工具配置
MAX_TOOL_CALLS_PER_TURN = 10    # 每轮最大工具调用次数
MAX_FILE_READ_BYTES = 200_000   # 文件读取大小限制 (200KB)
MAX_TOOL_RESULT_TOKENS = 4000   # 单个工具结果 token 上限
MAX_SEARCH_RESULTS = 50         # 搜索最大结果数
CODE_EXECUTION_TIMEOUT = 10     # 代码执行超时 (秒)
ALLOWED_PATH_PREFIX = None      # 文件操作限制目录（None=延迟求值到 os.getcwd()）
```

## 📝 设计文档

详见 [Design.md](Design.md)

## ❓ 常见问题

### Q: 如何获取 DeepSeek API Key？

A: 访问 [DeepSeek 官网](https://platform.deepseek.com/) 注册账号并获取 API Key。

### Q: 为什么工具调用没有显示？

A: 请确保已开启 Verbose 模式，输入 `/verbose` 命令切换。

### Q: 对话太长怎么办？

A: Agent 会自动裁剪旧消息以保持在 token 限制内，也可以手动 `/reset` 重置。

## 📄 License

MIT