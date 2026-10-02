"""
日志配置模块
配置 Python logging 模块，支持文件日志和控制台日志
"""

import logging
import sys
from pathlib import Path
from datetime import datetime


def setup_logging(
    log_file: str = "agent.log",
    console_level: int = logging.INFO,
    file_level: int = logging.DEBUG
) -> None:
    """配置日志系统

    Args:
        log_file: 日志文件路径
        console_level: 控制台日志级别
        file_level: 文件日志级别
    """
    # 创建日志目录
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # 获取根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # 清除现有的处理器
    root_logger.handlers.clear()

    # 创建格式化器
    file_formatter = logging.Formatter(
        '%(asctime)s | %(name)-20s | %(levelname)-8s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_formatter = logging.Formatter(
        '%(levelname)-8s | %(message)s'
    )

    # 文件处理器（详细日志）
    file_handler = logging.FileHandler(
        log_file,
        encoding='utf-8',
        mode='a'  # 追加模式
    )
    file_handler.setLevel(file_level)
    file_handler.setFormatter(file_formatter)

    # 控制台处理器（简洁日志）
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(console_level)
    console_handler.setFormatter(console_formatter)

    # 添加处理器
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # 记录启动信息
    logging.info("=" * 50)
    logging.info(f"日志系统初始化完成 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logging.info(f"日志文件: {log_file}")
    logging.info(f"控制台级别: {logging.getLevelName(console_level)}")
    logging.info(f"文件级别: {logging.getLevelName(file_level)}")
    logging.info("=" * 50)


def get_logger(name: str) -> logging.Logger:
    """获取指定名称的日志记录器

    Args:
        name: 日志记录器名称

    Returns:
        日志记录器实例
    """
    return logging.getLogger(name)