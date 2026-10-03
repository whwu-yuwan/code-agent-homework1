"""
CLI 交互界面
提供命令行交互入口，支持多轮对话、斜杠命令、Verbose 模式
"""

import sys
import logging
from datetime import datetime
from pathlib import Path

import config
from agent import CodeAgent
from exceptions import AgentError, APIError, ContextError, ConfigError
from callbacks import verbose_manager
from logger import setup_logging

# 创建日志记录器
logger = logging.getLogger(__name__)


BANNER = """
╔══════════════════════════════════════════════════════════════╗
║              🤖 代码解释 Agent (Code Explanation Agent)       ║
║                                                              ║
║  功能：读取代码文件、解释代码逻辑、生成注释、回答代码问题        ║
║                                                              ║
║  命令：                                                      ║
║    /help      - 显示帮助信息                                 ║
║    /reset     - 重置对话历史                                 ║
║    /verbose   - 切换详细模式（显示工具调用详情）               ║
║    /history   - 查看对话历史摘要                             ║
║    /save      - 保存对话记录到文件                           ║
║    /quit      - 退出程序                                     ║
║                                                              ║
║  提示：直接输入代码相关问题即可开始对话                         ║
╚══════════════════════════════════════════════════════════════╝
"""

HELP_TEXT = """
📖 帮助信息
───────────────────────────────────
命令：
  /help      - 显示此帮助信息
  /reset     - 重置对话历史（清除上下文）
  /verbose   - 切换详细模式（显示工具调用详情）
  /history   - 查看对话历史摘要
  /save      - 保存对话记录到文件
  /quit      - 退出程序

使用示例：
  "请解释 main.py 的代码逻辑"
  "这个项目有哪些文件？"
  "帮我看看 config.py 里有什么"
  "搜索代码中所有使用 logging 的地方"
  "解释一下这段代码：print('hello')"

提示：
  - 直接输入你的问题，Agent 会自动读取和分析代码
  - 支持多轮对话，Agent 会记住上下文
  - 输入 /verbose 可以查看工具调用详情
  - 输入 /reset 可以清除对话历史重新开始
───────────────────────────────────
"""


def check_api_key() -> None:
    """检查 API Key 是否已设置

    Raises:
        ConfigError: API Key 未设置
    """
    if not config.API_KEY:
        raise ConfigError(
            "未设置 DEEPSEEK_API_KEY 环境变量\n"
            "请按以下步骤设置：\n"
            "  Windows:  set DEEPSEEK_API_KEY=your-api-key-here\n"
            "  Linux/Mac: export DEEPSEEK_API_KEY=your-api-key-here"
        )


def handle_command(command: str, agent: CodeAgent) -> bool:
    """处理斜杠命令

    Args:
        command: 用户输入的命令（以 / 开头）
        agent: CodeAgent 实例

    Returns:
        True 表示应该退出程序，False 表示继续
    """
    command = command.strip().lower()

    if command in ("/quit", "/exit"):
        print("\n👋 再见！感谢使用代码解释 Agent！")
        return True

    elif command == "/reset":
        agent.reset()
        print("✅ 对话历史已重置")
        return False

    elif command == "/help":
        print(HELP_TEXT)
        return False

    elif command == "/verbose":
        is_verbose = verbose_manager.toggle()
        mode = "开启" if is_verbose else "关闭"
        print(f"✅ 详细模式已{mode}")
        if is_verbose:
            print("   将显示工具调用详情和 Agent 思考过程")
        return False

    elif command == "/history":
        print(agent.get_conversation_summary())
        if verbose_manager.verbose:
            summary = verbose_manager.get_summary()
            print(f"\n📊 工具调用统计:")
            print(f"  - 总调用次数: {summary['total_calls']}")
            print(f"  - 总耗时: {summary['total_time']:.2f}s")
        return False

    elif command == "/save":
        save_conversation(agent)
        return False

    else:
        print(f"❌ 未知命令: {command}")
        print("输入 /help 查看可用命令")
        return False


def save_conversation(agent: CodeAgent) -> None:
    """保存对话记录到文件"""
    try:
        save_dir = Path("conversations")
        save_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = save_dir / f"conversation_{timestamp}.txt"

        with open(filename, "w", encoding="utf-8") as f:
            f.write("=" * 60 + "\n")
            f.write("代码解释 Agent - 对话记录\n")
            f.write(f"保存时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 60 + "\n\n")

            for msg in agent.messages:
                if msg.type == "system":
                    f.write("[系统提示词]\n")
                    f.write("-" * 40 + "\n")
                    f.write(msg.content + "\n")
                    f.write("-" * 40 + "\n\n")
                elif msg.type == "human":
                    f.write(f"[用户] {msg.content}\n\n")
                elif msg.type == "ai":
                    f.write(f"[Agent] {msg.content}\n\n")
                elif msg.type == "tool":
                    f.write(f"[工具结果] {msg.content}\n\n")

            f.write("\n" + "=" * 60 + "\n")
            f.write("对话统计\n")
            f.write("=" * 60 + "\n")
            f.write(agent.get_conversation_summary() + "\n")

        print(f"✅ 对话记录已保存到: {filename}")
        logger.info(f"对话记录已保存到: {filename}")

    except Exception as e:
        print(f"❌ 保存失败: {e}")
        logger.error(f"保存对话记录失败: {e}")


def main():
    """主函数"""
    setup_logging(
        log_file=config.LOG_FILE,
        console_level=config.LOG_CONSOLE_LEVEL,
        file_level=config.LOG_FILE_LEVEL
    )

    print(BANNER)

    # 检查 API Key
    try:
        check_api_key()
    except ConfigError as e:
        print(f"❌ 配置错误: {e}")
        sys.exit(1)

    # 创建 Agent
    try:
        agent = CodeAgent()
        print("✅ Agent 初始化成功！")
        print("─" * 50)
        logger.info("Agent 初始化成功")
    except Exception as e:
        print(f"❌ Agent 初始化失败: {e}")
        logger.error(f"Agent 初始化失败: {e}")
        sys.exit(1)

    # 主循环
    while True:
        try:
            user_input = input("\n🧑 You > ").strip()

            if not user_input:
                continue

            if user_input.startswith("/"):
                if handle_command(user_input, agent):
                    break
                continue

            if not verbose_manager.verbose:
                print("\n🤔 思考中...")

            try:
                response = agent.chat(user_input)
                print(f"\n🤖 Agent:\n{response}")
                logger.info(f"Agent 回复完成，消息数: {agent.message_count}")
            except ContextError as e:
                print(f"\n⚠️ 输入错误: {e}")
                logger.warning(f"输入错误: {e}")
            except APIError as e:
                print(f"\n🌐 API 错误: {e}")
                logger.error(f"API 错误: {e}")
            except AgentError as e:
                print(f"\n❌ Agent 错误: {e}")
                logger.error(f"Agent 错误: {e}")

        except KeyboardInterrupt:
            print("\n\n👋 再见！（Ctrl+C）")
            break
        except EOFError:
            print("\n\n👋 再见！（EOF）")
            break


if __name__ == "__main__":
    main()