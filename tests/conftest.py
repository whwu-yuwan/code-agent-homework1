"""
测试配置
"""

import pytest
import os
import sys

# 确保项目根目录在 Python 路径中
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def tmp_text_file(tmp_path):
    """创建临时文本文件"""
    file_path = tmp_path / "test.py"
    file_path.write_text("print('hello world')\n", encoding="utf-8")
    return str(file_path)


@pytest.fixture
def tmp_dir_with_files(tmp_path):
    """创建包含多个文件的临时目录"""
    (tmp_path / "main.py").write_text("print('main')\n", encoding="utf-8")
    (tmp_path / "config.py").write_text("DEBUG = True\n", encoding="utf-8")
    (tmp_path / "subdir").mkdir()
    (tmp_path / "subdir" / "utils.py").write_text("def hello(): pass\n", encoding="utf-8")
    return str(tmp_path)