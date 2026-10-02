"""
CLI 交互界面
提供命令行交互入口，支持多轮对话和斜杠命令
"""

import sys

import config
from agent import CodeAgent, AgentError


BANNER = """
╔══════════════════════════════════════════════════════════════╗
║              🤖 代码解释 Agent (Code Explanation Agent)       ║
║                                                              ║
║  功能：读取代码文件、解释代码逻辑、生成注释、回答代码问题        ║
║                                                              ║
║  命令：                                                      ║
║    /help   - 显示帮助信息                                    ║
║    /reset  - 重置对话历史                                    ║
║    /quit   - 退出程序                                        ║
║                                                              ║
║  提示：直接输入代码相关问题即可开始对话                         ║
╚══════════════════════════════════════════════════════════════╝
"""

HELP_TEXT = """
📖 帮助信息
───────────────────────────────────
命令：
  /help   - 显示此帮助信息
  /reset  - 重置对话历史（清除上下文）
  /quit   - 退出程序

使用示例：
  "请解释 main.py 的代码逻辑"
  "这个项目有哪些文件？"
  "帮我看看 config.py 里有什么"
  "解释一下这段代码：print('hello')"
  "读取 tools.py 并解释 read_file 函数"

提示：
  - 直接输入你的问题，Agent 会自动读取和分析代码
  - 支持多轮对话，Agent 会记住上下文
  - 输入 /reset 可以清除对话历史重新开始
───────────────────────────────────
"""


def check_api_key() -> bool:
    """检查 API Key 是否已设置"""
    if not config.API_KEY:
        print("❌ 错误：未设置 DEEPSEEK_API_KEY 环境变量")
        print()
        print("请按以下步骤设置：")
        print("  Windows:  set DEEPSEEK_API_KEY=your-api-key-here")
        print("  Linux/Mac: export DEEPSEEK_API_KEY=your-api-key-here")
        print()
        print("或者在代码中直接设置（不推荐）：")
        print("  在 config.py 中将 API_KEY 设为你的 API Key")
        return False
    return True


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

    else:
        print(f"❌ 未知命令: {command}")
        print("输入 /help 查看可用命令")
        return False


def main():
    """主函数"""
    print(BANNER)

    # 检查 API Key
    if not check_api_key():
        sys.exit(1)

    # 创建 Agent
    try:
        agent = CodeAgent()
        print("✅ Agent 初始化成功！")
        print("─" * 50)
    except Exception as e:
        print(f"❌ Agent 初始化失败: {e}")
        sys.exit(1)

    # 主循环
    while True:
        try:
            # 获取用户输入
            user_input = input("\n🧑 You > ").strip()

            # 跳过空输入
            if not user_input:
                continue

            # 处理斜杠命令
            if user_input.startswith("/"):
                if handle_command(user_input, agent):
                    break
                continue

            # 调用 Agent
            print("\n🤔 思考中...")
            try:
                response = agent.chat(user_input)
                print(f"\n🤖 Agent:\n{response}")
            except AgentError as e:
                print(f"\n❌ Agent 错误: {e}")
            except Exception as e:
                print(f"\n❌ 未知错误: {e}")

        except KeyboardInterrupt:
            print("\n\n👋 再见！（Ctrl+C）")
            break
        except EOFError:
            print("\n\n👋 再见！（EOF）")
            break


if __name__ == "__main__":
    main()