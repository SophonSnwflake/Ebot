from dataclasses import dataclass
from typing import Optional


@dataclass
class CommandResult:
    handled: bool
    reply: Optional[str] = None


def try_handle_command(text: str, current_mode: str) -> CommandResult:
    """
    最小命令：
    - /ping
    - /help
    - /mode at|all
    """
    if not text.startswith("/"):
        return CommandResult(handled=False)

    parts = text.strip().split()
    cmd = parts[0].lower()

    if cmd == "/ping":
        return CommandResult(True, "我操你妈")

    if cmd == "/help":
        return CommandResult(
            True,
            "命令：/ping, /help, /mode at|all\n"
            f"当前触发模式：{current_mode}（at=仅@我触发，all=所有消息触发）"
        )

    if cmd == "/mode":
        if len(parts) < 2:
            return CommandResult(True, "用法：/mode at 或 /mode all")
        mode = parts[1].lower()
        if mode not in ("at", "all"):
            return CommandResult(True, "模式只能是 at 或 all")
        return CommandResult(True, f"SET_MODE::{mode}")  # 特殊返回给上层处理

    return CommandResult(True, "未知命令，试试 /help")