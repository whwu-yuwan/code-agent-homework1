"""
工具单元测试
"""

import pytest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools import read_file, list_directory, execute_python


class TestReadFile:
    """read_file 工具测试"""

    def test_read_existing_file(self, tmp_text_file):
        """测试读取存在的文件"""
        result = read_file.invoke({"file_path": tmp_text_file})
        assert "hello world" in result

    def test_read_nonexistent_file(self):
        """测试读取不存在的文件"""
        result = read_file.invoke({"file_path": "/nonexistent/file.py"})
        assert "错误" in result
        assert "不存在" in result

    def test_read_directory_as_file(self, tmp_path):
        """测试读取目录（应该报错）"""
        result = read_file.invoke({"file_path": str(tmp_path)})
        assert "错误" in result
        assert "不是文件" in result


class TestListDirectory:
    """list_directory 工具测试"""

    def test_list_directory(self, tmp_dir_with_files):
        """测试列出目录内容"""
        result = list_directory.invoke({"dir_path": tmp_dir_with_files})
        assert "main.py" in result
        assert "config.py" in result
        assert "subdir" in result

    def test_list_nonexistent_directory(self):
        """测试列出不存在的目录"""
        result = list_directory.invoke({"dir_path": "/nonexistent/dir"})
        assert "错误" in result
        assert "不存在" in result

    def test_list_empty_directory(self, tmp_path):
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
        """测试语法错误"""
        result = execute_python.invoke({"code": "def foo("})
        assert "错误" in result or "Error" in result

    def test_no_output(self):
        """测试无输出的代码"""
        result = execute_python.invoke({"code": "x = 1"})
        assert "无输出" in result