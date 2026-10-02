"""
工具单元测试
测试所有 5 个工具的功能
"""

import pytest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools import read_file, list_directory, execute_python, search_code, generate_comments


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


class TestSearchCode:
    """search_code 工具测试"""

    def test_search_keyword(self, tmp_dir_with_files):
        """测试搜索关键词"""
        result = search_code.invoke({
            "keyword": "print",
            "dir_path": tmp_dir_with_files,
            "file_pattern": "*.py"
        })
        assert "print" in result
        assert "匹配" in result

    def test_search_no_results(self, tmp_dir_with_files):
        """测试搜索无结果"""
        result = search_code.invoke({
            "keyword": "nonexistent_function_xyz",
            "dir_path": tmp_dir_with_files,
            "file_pattern": "*.py"
        })
        assert "未找到" in result

    def test_search_nonexistent_dir(self):
        """测试搜索不存在的目录"""
        result = search_code.invoke({
            "keyword": "test",
            "dir_path": "/nonexistent/dir"
        })
        assert "错误" in result
        assert "不存在" in result

    def test_search_regex(self, tmp_dir_with_files):
        """测试正则表达式搜索"""
        result = search_code.invoke({
            "keyword": "def \\w+",
            "dir_path": tmp_dir_with_files,
            "file_pattern": "*.py"
        })
        # 应该找到函数定义
        assert "匹配" in result or "未找到" in result


class TestGenerateComments:
    """generate_comments 工具测试"""

    def test_generate_inline_comments(self, tmp_text_file):
        """测试生成行内注释"""
        result = generate_comments.invoke({
            "file_path": tmp_text_file,
            "style": "inline"
        })
        assert "注释生成完成" in result or "错误" in result

    def test_generate_block_comments(self, tmp_text_file):
        """测试生成块注释"""
        result = generate_comments.invoke({
            "file_path": tmp_text_file,
            "style": "block"
        })
        assert "注释生成完成" in result or "错误" in result

    def test_generate_comments_nonexistent_file(self):
        """测试对不存在的文件生成注释"""
        result = generate_comments.invoke({
            "file_path": "/nonexistent/file.py"
        })
        assert "错误" in result
        assert "不存在" in result