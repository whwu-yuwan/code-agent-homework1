# 📐 设计文档 - 代码解释 Agent

## 1. 架构概述

### 1.1 系统架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                           用户 (CLI)                                 │
│                              │                                       │
│                              ▼                                       │
│                      ┌──────────────┐                                │
│                      │   main.py    │  CLI 交互界面                   │
│                      │              │  - 命令处理                     │
│                      │              │  - 异常分类捕获                 │
│                      └──────┬───────┘                                │
│                             │                                        │
│                             ▼                                        │
│                      ┌──────────────┐                                │
│                      │   agent.py   │  Agent 循环（核心）              │
│                      │              │  - 推理→工具→观察→再推理        │
│                      │              │  - 上下文裁剪（tiktoken）       │
│                      │              │  - Token 统计                   │
│                      │              │  - 轮次耗尽兜底                 │
│                      └──────┬───────┘                                │
│                             │                                        │
│        ┌────────────────────┼────────────────────┐                  │
│        ▼                    ▼                    ▼                  │
│ ┌──────────────┐   ┌──────────────┐   ┌──────────────┐             │
│ │  callbacks   │   │   tools.py   │   │  prompts.py  │             │
│ │  (回调系统)   │   │  (4个工具)    │   │  (系统提示词)  │             │
│ └──────────────┘   └──────────────┘   └──────────────┘             │
│        │                                                            │
│        ▼                                                            │
│ ┌──────────────┐   ┌──────────────┐                                │
│ │   logger     │   │  exceptions  │                                │
│ │  (日志系统)   │   │  (异常体系)   │                                │
│ └──────────────┘   └──────────────┘                                │
│        │                                                            │
│        ▼                                                            │
│  DeepSeek API (via langchain-openai)                                │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 组件职责

| 组件 | 文件 | 职责 |
|------|------|------|
| CLI 界面 | `main.py` | 命令行交互、异常分类捕获、对话保存 |
| Agent 核心 | `agent.py` | Agent 循环、上下文裁剪、Token 统计、异常抛出 |
| 工具模块 | `tools.py` | 4 个工具的声明式定义和执行 |
| 提示词 | `prompts.py` | 系统提示词定义 |
| 回调系统 | `callbacks.py` | LangChain 回调、Verbose 模式、工具名存储 |
| 日志系统 | `logger.py` | 文件日志 + 控制台日志 |
| 异常体系 | `exceptions.py` | 自定义异常类（被实际 raise 和 catch） |
| 配置 | `config.py` | 常量配置（均有引用） |

## 2. Agent 循环设计

### 2.1 核心流程

```
用户输入
    │
    ▼
添加到对话历史
    │
    ▼
上下文裁剪（tiktoken 估算，超阈值则裁剪旧消息对）
    │
    ▼
调用 LLM（带工具定义 + 回调）
    │
    ├─── 返回工具调用 ──→ 执行工具（传 callbacks）──→ 结果加入历史 ──→ 再次调用 LLM
    │         │
    │         ▼
    │   ┌──────────────┐
    │   │  callbacks   │  实时记录工具调用详情（名称、参数、耗时）
    │   └──────────────┘
    │
    ├─── 返回文本 ──→ 输出给用户
    │
    └─── 轮次耗尽 ──→ 调用不带 tools 的 LLM 强制生成回复
                      └── 失败则返回兜底消息
```

### 2.2 关键设计决策

1. **最大工具调用次数**：10 次，耗尽后不崩溃，强制生成回复
2. **上下文裁剪**：使用 tiktoken 估算 token，超过 51904 时裁剪（为输出和工具结果预留空间），保持 tool_call/tool_result 配对
3. **异常分层**：ToolError、APIError 分别在工具执行和 LLM 调用时抛出
4. **回调系统**：工具执行时传入 callbacks，确保 LangChain 触发回调事件

## 3. 工具设计

### 3.1 工具列表

| 工具 | 功能 | 参数 | 说明 |
|------|------|------|------|
| `read_file` | 读取本地代码文件 | `file_path: str` | 支持 UTF-8/Latin-1，大小限制 200KB |
| `list_directory` | 列出目录内容 | `dir_path: str` | 按目录/文件排序 |
| `execute_python` | 执行 Python 代码 | `code: str` | subprocess 隔离，10 秒超时 |
| `search_code` | 搜索代码关键词 | `keyword, dir_path, pattern` | 默认递归 `**/*.py`，最多 50 条结果 |

### 3.2 安全限制

- **路径白名单**：所有文件操作限制在工作目录（`os.getcwd()`）及其子目录下，超出范围抛出 ToolError
- **文件大小限制**：最大 200KB
- **代码执行超时**：10 秒（subprocess 级别）
- **搜索结果限制**：最多 50 条
- **安全风险提示**：`execute_python` 在独立子进程中执行代码（subprocess 隔离），无沙箱隔离，仅适合本地开发调试场景

## 4. Prompt 设计

### 4.1 系统提示词结构

```
角色定义：代码解释专家
    ↓
能力说明：文件读取、目录浏览、代码执行、代码搜索、注释生成
    ↓
工作流程：先读文件 → 再解释
    ↓
响应风格：Markdown、引用行号、中文
    ↓
重要规则：先读代码再解释、不猜测
```

## 5. 错误处理

### 5.1 异常类层次结构

```
AgentError (Agent 基础异常)
├── ToolError    — 工具执行失败、未知工具时 raise（tools.py）
├── APIError     — LLM 调用失败时 raise（agent.py）
├── ContextError — 输入过长时 raise（agent.py）
└── ConfigError  — 配置错误时 raise（main.py）
```

### 5.2 错误处理矩阵

| 场景 | 处理方式 | 异常类型 |
|------|----------|----------|
| API Key 未设置 | raise ConfigError，提示设置方法 | `ConfigError` |
| LLM 调用失败 | 捕获并 raise APIError | `APIError` |
| 输入过长 | raise ContextError | `ContextError` |
| 工具执行失败 | 工具内部 raise ToolError，Agent 捕获并转为 ToolMessage | `ToolError` |
| 未知工具 | Agent raise ToolError，转为 ToolMessage | `ToolError` |
| 工具轮次耗尽 | 调用不带 tools 的 LLM 强制回复 | - |
| 用户中断 (Ctrl+C) | 优雅退出 | - |

### 5.3 重试机制

使用 LangChain ChatOpenAI 的重试机制，显式设置 `max_retries=2, timeout=30`。工具执行不重试（工具失败通常是确定性错误，重试无意义）。

## 6. 上下文管理

### 6.1 消息类型

- `SystemMessage`：系统提示词（始终保留，不被裁剪）
- `HumanMessage`：用户输入
- `AIMessage`：Agent 回复（可能包含 tool_calls）
- `ToolMessage`：工具执行结果

### 6.2 裁剪策略

- **估算方式**：使用 tiktoken `cl100k_base` 编码估算 token
- **裁剪阈值**：`MAX_CONTEXT_TOKENS - MAX_OUTPUT_TOKENS - TOOL_RESULT_RESERVE_TOKENS`（64000 - 4096 - 8000 = 51904），为输出和工具结果预留空间
- **裁剪规则**：从旧到新删除，保持 tool_call + tool_result 配对不被拆散
- **保护**：SystemMessage（第一条）永不被裁剪；当前问题组（最后一条 HumanMessage 及其后续消息）受显式保护

## 7. 回调系统

### 7.1 回调处理器

```
ToolCallbackHandler
├── on_tool_start()    # 记录 run_id→tool_name 映射，显示工具名和参数
├── on_tool_end()      # 从映射获取真实工具名（非 "unknown"），显示耗时和结果
├── on_tool_error()    # 显示错误信息
├── on_llm_start()     # 显示 "思考中..."
├── on_llm_end()       # 显示 token 使用量
└── get_summary()      # 获取工具调用统计
```

### 7.2 关键实现

- 工具执行时传入 `config={"callbacks": callbacks}`，确保 LangChain 触发回调
- `on_tool_start` 存储 `run_id → tool_name` 映射，`on_tool_end` 从中获取真实名称

## 8. 日志系统

### 8.1 日志级别

- **DEBUG**：详细调试信息（仅文件）
- **INFO**：一般信息（控制台 + 文件）
- **WARNING**：警告（如轮次耗尽）
- **ERROR**：错误（工具失败、API 失败）

## 9. 测试策略

### 9.1 测试覆盖

| 测试类型 | 文件 | 用例数 | 覆盖范围 |
|----------|------|--------|----------|
| 工具测试 | `test_tools.py` | 14 | 4 个工具的功能和边界 |
| Agent 测试 | `test_agent.py` | 9 | 简单回复、工具循环、重置、轮次耗尽兜底、输入过长、上下文裁剪、工具错误回灌、token 统计、API 失败清理 |

### 9.2 测试方法

- **Mock LLM**：使用 `unittest.mock.patch` 模拟 ChatOpenAI
- **Mock 工具**：验证 `.invoke()` 被正确调用（参数、config）
- **临时文件**：使用 pytest `tmp_path` fixture
- **边界测试**：文件不存在、空目录、语法错误、递归搜索

### 9.3 断言质量

- 所有断言验证具体返回内容（非恒真形式），部分断言使用 `or` 覆盖中英文环境差异
- 工具测试验证具体返回内容（如文件名、关键词、错误标识）
- Agent 测试验证 `.invoke()` 调用参数（参数、config）