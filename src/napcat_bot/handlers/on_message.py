from typing import Any, Dict, Optional
import asyncio

from .filters import extract_plain_text, is_at_me, strip_at_me
from .commands import try_handle_command
from ..services.llm_client import LLMClient, LLMRequest
from ..services.state import RuntimeState


async def handle_group_message(
    ws,
    evt: Dict[str, Any],
    state: RuntimeState,
    llm: LLMClient,
    memory_store=None,  # 新增：可选的记忆存储对象（MemoryStore）
) -> Optional[str]:
    """
    返回要回复的文本；返回 None 表示不回复
    """
    group_id = int(evt.get("group_id", 0))
    user_id = int(evt.get("user_id", 0))

    text = extract_plain_text(evt)
    if not text:
        return None

    # 1) 先做命令（命令优先，不受触发模式限制）
    cmd_res = try_handle_command(text, state.trigger_mode)
    if cmd_res.handled:
        if cmd_res.reply and cmd_res.reply.startswith("SET_MODE::"):
            new_mode = cmd_res.reply.split("::", 1)[1]
            state.trigger_mode = new_mode
            return f"已切换触发模式为：{new_mode}"
        return cmd_res.reply

    # 2) 再做触发判定（at 模式下必须 @我）
    if state.trigger_mode == "at":
        if not is_at_me(evt):
            return None
        text = strip_at_me(text)
        if not text:
            return None

    # 3) 先 recall（检索记忆）
    memories: list[str] = []
    if memory_store is not None:
        try:
            memories = await memory_store.recall(group_id=group_id, query=text)
        except Exception as e:
            # 记忆检索失败不应该让 bot 整体崩掉，降级继续走 LLM
            print(f"[memory] recall failed: {e}")

    # 4) 再 call LLM（把 memories 一起传进去）
    try:
        reply = await llm.generate(
            LLMRequest(
                user_id=user_id,
                group_id=group_id,
                text=text,
                memories=memories,  # 需要你在 LLMRequest 里加这个字段
            )
        )
    except Exception as e:
        import traceback
        print(f"[llm] generate failed: {type(e).__name__}: {e}")
        traceback.print_exc()
        return "我刚刚想了一下但脑子短路了，稍后再试试 😵"

    # 5) 最后异步写入记忆（不阻塞回复）
    if memory_store is not None:
        async def _safe_add_user():
            try:
                await memory_store.add_memory(group_id=group_id, user_id=user_id, role="user", content=text)
            except Exception as e:
                print(f"[memory] add user memory failed: {e}")

        async def _safe_add_bot():
            try:
                await memory_store.add_memory(group_id=group_id, user_id=0, role="bot", content=reply)
            except Exception as e:
                print(f"[memory] add bot memory failed: {e}")

        asyncio.create_task(_safe_add_user())
        asyncio.create_task(_safe_add_bot())

    return reply