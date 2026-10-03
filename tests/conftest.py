"""
测试配置
"""

import pytest
import os
import sys

# 确保项目根目录在 Python 路径中
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def disable_path_restriction(monkeypatch):
    """测试时禁用路径白名单限制（临时文件在系统 temp 目录下）"""
    import config
    monkeypatch.setattr(config, 'ALLOWED_PATH_PREFIX', "/")


@pytest.fixture
def tmp_text_file(tmp_path):
    """创建临时 Python 文件"""
    file_path = tmp_path / "test.py"
    file_path.write_text("print('hello world')\n", encoding="utf-8")
    return str(file_path)


@pytest.fixture
def tmp_function_file(tmp_path):
    """创建包含函数定义的临时文件"""
    file_path = tmp_path / "sample.py"
    file_path.write_text(
        "def greet(name):\n"
        "    return f'Hello, {name}'\n"
        "\n"
        "class Calculator:\n"
        "    def add(self, a, b):\n"
        "        return a + b\n",
        encoding="utf-8"
    )
    return str(file_path)


@pytest.fixture
def tmp_dir_with_files(tmp_path):
    """创建包含多个文件和子目录的临时目录"""
    (tmp_path / "main.py").write_text("print('main')\n", encoding="utf-8")
    (tmp_path / "config.py").write_text("DEBUG = True\n", encoding="utf-8")
    (tmp_path / "subdir").mkdir()
    (tmp_path / "subdir" / "utils.py").write_text("def hello(): pass\n", encoding="utf-8")
    return str(tmp_path)