"""
自定义工具模块
使用 LangChain @tool 装饰器实现文件读取、目录浏览、代码执行工具
"""

import os
import sys
import subprocess
from pathlib import Path

from langchain_core.tools import tool

import config


@tool
def read_file(file_path: str) -> str:
    """读取本地代码文件的内容。
    当你需要查看代码文件、配置文件或任何文本文件时使用此工具。

    Args:
        file_path: 要读取的文件路径（相对路径或绝对路径）
    """
    try:
        path = Path(file_path).resolve()

        if not path.exists():
            return f"[错误] 文件不存在: {file_path}"

        if not path.is_file():
            return f"[错误] 路径不是文件: {file_path}"

        file_size = path.stat().st_size
        if file_size > config.MAX_FILE_READ_BYTES:
            size_mb = file_size / (1024 * 1024)
            return f"[错误] 文件过大 ({size_mb:.1f}MB)，超过限制 ({config.MAX_FILE_READ_BYTES / 1024 / 1024:.0f}MB)"

        # 尝试 UTF-8 编码，失败则用 latin-1
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            content = path.read_text(encoding="latin-1")

        return content

    except PermissionError:
        return f"[错误] 没有权限读取文件: {file_path}"
    except OSError as e:
        return f"[错误] 读取文件失败: {e}"


@tool
def list_directory(dir_path: str) -> str:
    """列出目录中的文件和子目录。
    当你需要了解项目结构或查找文件时使用此工具。

    Args:
        dir_path: 要列出的目录路径（相对路径或绝对路径）
    """
    try:
        path = Path(dir_path).resolve()

        if not path.exists():
            return f"[错误] 目录不存在: {dir_path}"

        if not path.is_dir():
            return f"[错误] 路径不是目录: {dir_path}"

        entries = sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))

        if not entries:
            return "(空目录)"

        lines = []
        for entry in entries:
            if entry.is_dir():
                lines.append(f"[目录] {entry.name}/")
            else:
                size = entry.stat().st_size
                if size < 1024:
                    size_str = f"{size}B"
                elif size < 1024 * 1024:
                    size_str = f"{size / 1024:.1f}KB"
                else:
                    size_str = f"{size / (1024 * 1024):.1f}MB"
                lines.append(f"[文件] {entry.name}  ({size_str})")

        return "\n".join(lines)

    except PermissionError:
        return f"[错误] 没有权限访问目录: {dir_path}"
    except OSError as e:
        return f"[错误] 访问目录失败: {e}"


@tool
def execute_python(code: str) -> str:
    """执行 Python 代码并返回输出。
    当你需要运行代码片段、验证逻辑或测试代码时使用此工具。

    Args:
        code: 要执行的 Python 代码
    """
    try:
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            timeout=config.CODE_EXECUTION_TIMEOUT,
            cwd=os.getcwd()
        )

        output = ""
        if result.stdout:
            output += result.stdout
        if result.stderr:
            if output:
                output += "\n--- stderr ---\n"
            output += result.stderr

        return output if output else "(无输出)"

    except subprocess.TimeoutExpired:
        return f"[错误] 代码执行超时（超过 {config.CODE_EXECUTION_TIMEOUT} 秒）"
    except Exception as e:
        return f"[错误] 执行失败: {e}"


# 工具列表，供 Agent 使用
TOOLS = [read_file, list_directory, execute_python]