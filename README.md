# 🤖 代码解释 Agent (Code Explanation Agent)

一个基于 LangChain 和 DeepSeek API 的代码解释助手 Agent，能够读取代码文件、解释代码逻辑、生成注释、回答代码相关问题。

## ✨ 功能特性

### 核心功能
- **代码读取**：自动读取本地代码文件内容
- **代码解释**：理解代码逻辑，用清晰的中文解释
- **目录浏览**：查看项目结构，了解文件组织
- **代码执行**：运行 Python 代码片段，验证逻辑
- **代码搜索**：在文件中搜索关键词或正则表达式
- **注释生成**：为代码文件自动生成详细注释

### 高级功能
- **多轮对话**：支持上下文记忆，连续提问
- **Verbose 模式**：显示工具调用详情和 Agent 思考过程
- **对话历史**：查看对话摘要和统计信息
- **对话保存**：导出对话记录到文件
- **日志系统**：完整的日志记录和错误追踪
- **错误处理**：API 调用失败自动重试，工具执行异常优雅处理

## 🛠️ 技术栈

- **Python 3.10+**
- **LangChain**：Agent 框架（Agent 执行、工具绑定、上下文管理）
- **DeepSeek API**：大语言模型（通过 OpenAI 兼容接口）
- **LangChain OpenAI**：连接 DeepSeek API
- **tiktoken**：Token 使用统计

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

### 示例 1：解释代码文件

```
🧑 You > 请解释 main.py 的代码逻辑

🤔 思考中...

🔧 调用工具: read_file
   参数: {'file_path': 'main.py'}
   ✅ 完成 (0.01s)
   结果: """
CLI 交互界面
提供命令行交互入口，支持多轮对话、斜杠命令、Verbose 模式
...

🤖 Agent:
## 概述
main.py 是程序的入口文件，实现了命令行交互界面。

## 核心逻辑
1. `check_api_key()` - 检查 API Key 是否设置
2. `handle_command()` - 处理斜杠命令（/help, /reset, /quit 等）
3. `main()` - 主循环，处理用户输入

## 关键代码
- 第 96-118 行：主循环实现
- 第 65-93 行：命令处理逻辑
```

### 示例 2：搜索代码

```
🧑 You > 搜索代码中所有使用 logging 的地方

🔧 调用工具: search_code
   参数: {'keyword': 'logging', 'dir_path': '.', 'file_pattern': '*.py'}
   ✅ 完成 (0.05s)
   结果: 共找到 15 处匹配...

🤖 Agent:
找到了 15 处使用 logging 的地方，主要分布在：
1. `logger.py` - 日志配置模块
2. `agent.py` - Agent 核心模块
3. `main.py` - CLI 界面
...
```

### 示例 3：生成注释

```
🧑 You > 为 tools.py 生成注释

🔧 调用工具: generate_comments
   参数: {'file_path': 'tools.py', 'style': 'inline'}
   ✅ 完成 (0.02s)

🤖 Agent:
已为 tools.py 生成注释，包含：
- 文件头注释
- 函数/类定义注释
- 关键逻辑注释
...
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
├── agent.py             # Agent 初始化与循环（核心）
├── tools.py             # 自定义工具（5个工具）
├── prompts.py           # 系统提示词
├── config.py            # 配置常量
├── callbacks.py         # LangChain 回调处理器
├── logger.py            # 日志配置模块
├── exceptions.py        # 自定义异常类
├── requirements.txt     # 依赖
├── README.md            # 项目文档
├── Design.md            # 设计文档
├── .gitignore
├── logs/                # 日志目录
│   └── agent.log        # 日志文件
├── conversations/       # 对话记录目录
└── tests/               # 测试
    ├── test_tools.py    # 工具测试
    └── test_agent.py    # Agent 测试
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
API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
MODEL_NAME = "deepseek-chat"

# 上下文管理
MAX_CONTEXT_TOKENS = 64000
TRIM_THRESHOLD_TOKENS = 50000

# 工具配置
MAX_TOOL_CALLS_PER_TURN = 10
MAX_FILE_READ_BYTES = 1_000_000  # 1MB
CODE_EXECUTION_TIMEOUT = 10  # 秒

# 日志配置
LOG_FILE = "logs/agent.log"
LOG_CONSOLE_LEVEL = 20  # INFO
LOG_FILE_LEVEL = 10  # DEBUG
```

## 📝 设计文档

详见 [Design.md](Design.md)

## ❓ 常见问题

### Q: 如何获取 DeepSeek API Key？

A: 访问 [DeepSeek 官网](https://platform.deepseek.com/) 注册账号并获取 API Key。

### Q: 为什么工具调用没有显示？

A: 请确保已开启 Verbose 模式，输入 `/verbose` 命令切换。

### Q: 如何查看日志？

A: 日志文件位于 `logs/agent.log`，包含详细的执行记录。

### Q: 对话记录保存在哪里？

A: 对话记录保存在 `conversations/` 目录下，文件名格式为 `conversation_YYYYMMDD_HHMMSS.txt`。

## 📄 License

MIT