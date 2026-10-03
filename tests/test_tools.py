"""
工具单元测试
测试所有 4 个工具的功能
"""

import pytest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools import read_file, list_directory, execute_python, search_code
from exceptions import ToolError


class TestReadFile:
    """read_file 工具测试"""

    def test_read_existing_file(self, tmp_text_file, disable_path_restriction):
        """测试读取存在的文件"""
        result = read_file.invoke({"file_path": tmp_text_file})
        assert "hello world" in result

    def test_read_nonexistent_file(self, disable_path_restriction):
        """测试读取不存在的文件 → 应抛出 ToolError"""
        with pytest.raises(ToolError, match="文件不存在"):
            read_file.invoke({"file_path": "/nonexistent/file.py"})

    def test_read_directory_as_file(self, tmp_path, disable_path_restriction):
        """测试读取目录（应该抛出 ToolError）"""
        with pytest.raises(ToolError, match="路径不是文件"):
            read_file.invoke({"file_path": str(tmp_path)})

    def test_read_outside_workspace(self, tmp_path, monkeypatch):
        """测试读取工作目录外的文件 → 应抛出 ToolError（路径白名单生效）"""
        import config
        # 设置白名单为 tmp_path，然后尝试读取 tmp_path 外的文件
        monkeypatch.setattr(config, 'ALLOWED_PATH_PREFIX', str(tmp_path))
        with pytest.raises(ToolError, match="超出允许范围"):
            read_file.invoke({"file_path": "/etc/hosts"})


class TestListDirectory:
    """list_directory 工具测试"""

    def test_list_directory(self, tmp_dir_with_files, disable_path_restriction):
        """测试列出目录内容"""
        result = list_directory.invoke({"dir_path": tmp_dir_with_files})
        assert "main.py" in result
        assert "config.py" in result
        assert "subdir" in result

    def test_list_nonexistent_directory(self, disable_path_restriction):
        """测试列出不存在的目录 → 应抛出 ToolError"""
        with pytest.raises(ToolError, match="目录不存在"):
            list_directory.invoke({"dir_path": "/nonexistent/dir"})

    def test_list_empty_directory(self, tmp_path, disable_path_restriction):
        """测试列出空目录"""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        result = list_directory.invoke({"dir_path": str(empty_dir)})
        assert "空目录" in result


class TestExecutePython:
    """execute_python 工具测试"""

    def test_simple_execution(self):
        """测试简单代码执行"""
        result = execute_python.invoke({"code": "print(2 + 3)"})
        assert "5" in result

    def test_syntax_error(self):
        """测试语法错误（subprocess 返回 stderr，不抛异常）"""
        result = execute_python.invoke({"code": "def foo("})
        assert result  # 非空，stderr 中包含错误信息

    def test_no_output(self):
        """测试无输出的代码"""
        result = execute_python.invoke({"code": "x = 1"})
        assert "无输出" in result


class TestSearchCode:
    """search_code 工具测试"""

    def test_search_keyword(self, tmp_dir_with_files, disable_path_restriction):
        """测试搜索关键词 - 应该找到匹配"""
        result = search_code.invoke({
            "keyword": "print",
            "dir_path": tmp_dir_with_files,
            "file_pattern": "**/*.py"
        })
        assert "匹配" in result
        assert "未找到" not in result

    def test_search_no_results(self, tmp_dir_with_files, disable_path_restriction):
        """测试搜索无结果"""
        result = search_code.invoke({
            "keyword": "nonexistent_function_xyz",
            "dir_path": tmp_dir_with_files,
            "file_pattern": "**/*.py"
        })
        assert "未找到" in result

    def test_search_nonexistent_dir(self, disable_path_restriction):
        """测试搜索不存在的目录 → 应抛出 ToolError"""
        with pytest.raises(ToolError, match="目录不存在"):
            search_code.invoke({
                "keyword": "test",
                "dir_path": "/nonexistent/dir"
            })

    def test_search_recursive(self, tmp_dir_with_files, disable_path_restriction):
        """测试递归搜索子目录"""
        result = search_code.invoke({
            "keyword": "hello",
            "dir_path": tmp_dir_with_files,
            "file_pattern": "**/*.py"
        })
        assert "匹配" in result
        assert "hello" in result

    def test_search_regex_fallback(self, tmp_dir_with_files, disable_path_restriction):
        """测试非法正则回退为字面量搜索"""
        # "[invalid" 是非法正则，应回退为字面量搜索
        result = search_code.invoke({
            "keyword": "[invalid",
            "dir_path": tmp_dir_with_files,
            "file_pattern": "**/*.py"
        })
        # 不应抛异常，应正常返回（无匹配或有匹配）
        assert isinstance(result, str)


class TestExecutePythonTimeout:
    """execute_python 超时测试"""

    def test_execute_python_timeout(self):
        """测试代码执行超时抛出 ToolError"""
        import config
        # 使用极短超时（通过 monkeypatch 不适用，直接用超时代码）
        # 用 sleep 超过 CODE_EXECUTION_TIMEOUT
        code = f"import time; time.sleep({config.CODE_EXECUTION_TIMEOUT + 5})"
        with pytest.raises(ToolError, match="超时"):
            execute_python.invoke({"code": code})


class TestReadFileLarge:
    """read_file 大文件测试"""

    def test_read_file_too_large(self, tmp_path, disable_path_restriction):
        """测试读取超大文件抛出 ToolError"""
        import config
        # 创建一个超过 MAX_FILE_READ_BYTES 的文件
        large_file = tmp_path / "large.py"
        large_file.write_bytes(b"x" * (config.MAX_FILE_READ_BYTES + 1))
        with pytest.raises(ToolError, match="文件过大"):
            read_file.invoke({"file_path": str(large_file)})