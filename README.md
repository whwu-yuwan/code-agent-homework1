# 🤖 代码解释 Agent (Code Explanation Agent)

一个基于 LangChain 和 DeepSeek API 的代码解释助手 Agent，能够读取代码文件、解释代码逻辑、生成注释、回答代码相关问题。

## ✨ 功能特性

- **代码读取**：自动读取本地代码文件内容
- **代码解释**：理解代码逻辑，用清晰的中文解释
- **目录浏览**：查看项目结构，了解文件组织
- **代码执行**：运行 Python 代码片段，验证逻辑
- **多轮对话**：支持上下文记忆，连续提问
- **错误处理**：API 调用失败自动重试，工具执行异常优雅处理

## 🛠️ 技术栈

- **Python 3.10+**
- **LangChain**：Agent 框架（Agent 执行、工具绑定、上下文管理）
- **DeepSeek API**：大语言模型（通过 OpenAI 兼容接口）
- **LangChain OpenAI**：连接 DeepSeek API

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

```
🧑 You > 请解释 main.py 的代码逻辑

🤔 思考中...

🤖 Agent:
## 概述
main.py 是程序的入口文件，实现了命令行交互界面...

## 核心逻辑
1. check_api_key() - 检查 API Key 是否设置
2. main() - 主循环，处理用户输入
...
```

## 🎯 命令说明

| 命令 | 说明 |
|------|------|
| `/help` | 显示帮助信息 |
| `/reset` | 重置对话历史（清除上下文） |
| `/quit` | 退出程序 |

## 📁 项目结构

```
code-agent-homework1/
├── main.py              # 入口，CLI 交互界面
├── agent.py             # Agent 初始化与循环（核心）
├── tools.py             # 自定义工具（文件读取、目录浏览、代码执行）
├── prompts.py           # 系统提示词
├── config.py            # 配置常量
├── requirements.txt     # 依赖
├── README.md            # 项目文档
├── Design.md            # 设计文档
└── tests/               # 测试
    ├── test_tools.py    # 工具测试
    └── test_agent.py    # Agent 测试
```

## 🧪 运行测试

```bash
pytest tests/ -v
```

## 📝 设计文档

详见 [Design.md](Design.md)

## 📄 License

MIT