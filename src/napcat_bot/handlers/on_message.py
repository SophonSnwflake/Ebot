from typing import Any, Dict, Optional

from .filters import extract_plain_text, is_at_me, strip_at_me
from .commands import try_handle_command
from ..services.llm_client import LLMClient, LLMRequest
from ..services.state import RuntimeState


async def handle_group_message(
    ws,
    evt: Dict[str, Any],
    state: RuntimeState,
    llm: LLMClient,
) -> Optional[str]:
    """
    返回要回复的文本；返回 None 表示不回复
    """
    group_id = int(evt.get("group_id", 0))
    user_id = int(evt.get("user_id", 0))

    text = extract_plain_text(evt)
    if not text:
        return None

    # 先做命令（不受触发模式限制，你也可以改成只在 @ 时命令才生效）
    cmd_res = try_handle_command(text, state.trigger_mode)
    if cmd_res.handled:
        if cmd_res.reply and cmd_res.reply.startswith("SET_MODE::"):
            new_mode = cmd_res.reply.split("::", 1)[1]
            state.trigger_mode = new_mode
            return f"已切换触发模式为：{new_mode}"
        return cmd_res.reply

    # 再做触发判定
    if state.trigger_mode == "at":
        if not is_at_me(evt):
            return None
        text = strip_at_me(text)
        if not text:
            return None

    # 走 LLM（目前是 DummyLLM 回显）
    reply = await llm.generate(LLMRequest(user_id=user_id, group_id=group_id, text=text))
    return reply