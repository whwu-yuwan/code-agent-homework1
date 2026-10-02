"""
自定义工具模块
使用 LangChain @tool 装饰器实现代码解释相关的工具集
"""

import os
import re
import sys
import subprocess
from pathlib import Path
from typing import Optional

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


@tool
def search_code(keyword: str, dir_path: str = ".", file_pattern: str = "*.py") -> str:
    """在代码文件中搜索关键词或正则表达式。
    当你需要查找某个函数、变量或代码片段的位置时使用此工具。

    Args:
        keyword: 要搜索的关键词或正则表达式
        dir_path: 搜索的目录路径（默认当前目录）
        file_pattern: 文件匹配模式（默认 *.py）
    """
    try:
        path = Path(dir_path).resolve()

        if not path.exists():
            return f"[错误] 目录不存在: {dir_path}"

        if not path.is_dir():
            return f"[错误] 路径不是目录: {dir_path}"

        # 编译正则表达式
        try:
            pattern = re.compile(keyword)
        except re.error:
            # 如果正则无效，当作普通字符串搜索
            pattern = re.compile(re.escape(keyword))

        results = []
        match_count = 0

        # 使用 glob 匹配文件
        for file_path in path.glob(file_pattern):
            if not file_path.is_file():
                continue

            # 跳过过大的文件
            if file_path.stat().st_size > config.MAX_FILE_READ_BYTES:
                continue

            try:
                content = file_path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, PermissionError):
                continue

            # 逐行搜索
            for line_num, line in enumerate(content.splitlines(), 1):
                if pattern.search(line):
                    match_count += 1
                    # 相对路径显示
                    try:
                        rel_path = file_path.relative_to(Path.cwd())
                    except ValueError:
                        rel_path = file_path
                    results.append(f"{rel_path}:{line_num}: {line.strip()}")

                    # 限制结果数量
                    if match_count >= 50:
                        results.append(f"\n... 共找到 {match_count}+ 处匹配（已截断）")
                        return "\n".join(results)

        if not results:
            return f"未找到匹配 '{keyword}' 的结果"

        return f"共找到 {match_count} 处匹配:\n" + "\n".join(results)

    except Exception as e:
        return f"[错误] 搜索失败: {e}"


@tool
def generate_comments(file_path: str, style: str = "inline") -> str:
    """为代码文件生成详细注释。
    当你需要快速理解代码或添加注释时使用此工具。

    Args:
        file_path: 要注释的代码文件路径
        style: 注释风格 - "inline"（行内注释）或 "block"（块注释/文档字符串）
    """
    try:
        path = Path(file_path).resolve()

        if not path.exists():
            return f"[错误] 文件不存在: {file_path}"

        if not path.is_file():
            return f"[错误] 路径不是文件: {file_path}"

        # 读取文件内容
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            content = path.read_text(encoding="latin-1")

        lines = content.splitlines()
        if not lines:
            return "文件为空，无需注释"

        # 根据文件扩展名确定注释符号
        ext = path.suffix.lower()
        comment_map = {
            ".py": "#",
            ".js": "//",
            ".ts": "//",
            ".java": "//",
            ".c": "//",
            ".cpp": "//",
            ".h": "//",
            ".go": "//",
            ".rs": "//",
            ".rb": "#",
            ".sh": "#",
            ".yaml": "#",
            ".yml": "#",
            ".toml": "#",
            ".json": "//",  # JSON 不支持注释，但用于显示
        }
        comment_prefix = comment_map.get(ext, "#")

        # 生成注释内容
        result_lines = []
        in_function = False
        func_indent = ""

        for i, line in enumerate(lines, 1):
            stripped = line.strip()

            # 检测函数/类定义
            if stripped.startswith(("def ", "class ", "function ", "async def ")):
                in_function = True
                func_indent = line[: len(line) - len(line.lstrip())]

                if style == "block":
                    # 块注释风格
                    if stripped.startswith("def ") or stripped.startswith("async def "):
                        func_name = stripped.split("(")[0].replace("def ", "").replace("async ", "")
                        result_lines.append(f"{func_indent}# TODO: 添加函数文档字符串")
                        result_lines.append(f'{func_indent}"""')
                        result_lines.append(f"{func_indent}{func_name} 函数")
                        result_lines.append(f"{func_indent}")
                        result_lines.append(f"{func_indent}Args:")
                        result_lines.append(f"{func_indent}    参数说明")
                        result_lines.append(f"{func_indent}")
                        result_lines.append(f"{func_indent}Returns:")
                        result_lines.append(f"{func_indent}    返回值说明")
                        result_lines.append(f'{func_indent}"""')
                    elif stripped.startswith("class "):
                        class_name = stripped.split("(")[0].replace("class ", "").replace(":", "")
                        result_lines.append(f"{func_indent}# TODO: 添加类文档字符串")
                        result_lines.append(f'{func_indent}"""')
                        result_lines.append(f"{func_indent}{class_name} 类")
                        result_lines.append(f"{func_indent}")
                        result_lines.append(f"{func_indent}Attributes:")
                        result_lines.append(f"{func_indent}    属性说明")
                        result_lines.append(f'{func_indent}"""')
                else:
                    # 行内注释风格
                    if stripped.startswith("def ") or stripped.startswith("async def "):
                        func_name = stripped.split("(")[0].replace("def ", "").replace("async ", "")
                        result_lines.append(f"{line}  # {func_name} 函数")
                    elif stripped.startswith("class "):
                        class_name = stripped.split("(")[0].replace("class ", "").replace(":", "")
                        result_lines.append(f"{line}  # {class_name} 类定义")
                continue

            # 检测复杂逻辑（条件、循环）
            if in_function and stripped:
                if stripped.startswith(("if ", "elif ", "else:", "for ", "while ", "try:", "except ", "finally:")):
                    if style == "inline":
                        result_lines.append(f"{line}  # 条件/循环逻辑")
                    else:
                        result_lines.append(line)
                    continue

                # 检测 return 语句
                if stripped.startswith("return "):
                    if style == "inline":
                        result_lines.append(f"{line}  # 返回结果")
                    else:
                        result_lines.append(line)
                    continue

            result_lines.append(line)

        # 添加文件头注释
        header = f"{comment_prefix} 文件: {path.name}\n"
        header += f"{comment_prefix} 说明: 由代码解释 Agent 自动生成的注释\n"
        header += f"{comment_prefix} 注意: 请根据实际情况修改注释内容\n"

        final_content = header + "\n".join(result_lines)

        # 生成注释后的文件路径
        commented_path = path.parent / f"{path.stem}_commented{path.suffix}"

        return f"注释生成完成！\n\n注释后的代码:\n\n{final_content}\n\n建议保存到: {commented_path}"

    except Exception as e:
        return f"[错误] 注释生成失败: {e}"


# 工具列表，供 Agent 使用
TOOLS = [read_file, list_directory, execute_python, search_code, generate_comments]