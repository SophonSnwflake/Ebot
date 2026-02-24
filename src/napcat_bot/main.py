import asyncio
from logging import config
from typing import Any, Dict

from .config import load_config
from .adapter.onebot_ws_server import OneBotReverseWSServer
from .services.state import RuntimeState
from .services.reply import send_group_text
from .handlers.on_message import handle_group_message
from .services.llm_client import DummyLLMClient, OpenAICompatLLMClient

async def _amain() -> None:
    cfg = load_config()
    state = RuntimeState(trigger_mode=cfg.trigger_mode)
    if cfg.llm_base_url and cfg.llm_api_key and cfg.llm_model:
        llm = OpenAICompatLLMClient(
            base_url=cfg.llm_base_url,
            api_key=cfg.llm_api_key,
            model=cfg.llm_model,
            prefix=cfg.reply_prefix,
        )
    else:
        llm = DummyLLMClient(prefix=cfg.reply_prefix)
        
    async def on_event(ws, evt: Dict[str, Any]) -> None:
        if evt.get("post_type") != "message":
            return
        if evt.get("message_type") != "group":
            return
        group_id = int(evt.get("group_id", 0))
        if group_id == 0:
            return

        lock = state.lock_for_group(group_id)
        async with lock:
            reply_text = await handle_group_message(ws, evt, state, llm)
            if reply_text:
                await send_group_text(ws, group_id, reply_text)

    server = OneBotReverseWSServer(cfg.host, cfg.port, cfg.access_token)
    server.set_event_handler(on_event)

    print(f">>> OneBot reverse WS server listening on ws://{cfg.host}:{cfg.port}")
    await server.serve_forever()

def run() -> None:
    asyncio.run(_amain())


