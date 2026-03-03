import asyncio
from typing import Any, Dict

from .config import load_config
from .adapter.onebot_ws_server import OneBotReverseWSServer
from .services.state import RuntimeState
from .services.llm_client import OpenAICompatLLMClient, DummyLLMClient
from .services.reply import send_group_text
from .services.db import create_pg_pool
from .services.memory import MemoryStore, MemoryConfig
from .handlers.on_message import handle_group_message


async def _amain() -> None:
    cfg = load_config()
    print("[CFG] llm_base_url =", cfg.llm_base_url)
    print("[CFG] llm_model =", cfg.llm_model)
    print("[CFG] llm_key_set =", bool(cfg.llm_api_key))
    print("[CFG] trigger_mode =", cfg.trigger_mode)
    # 1) Postgres + pgvector memory
    pool = await create_pg_pool(cfg.pg_dsn)
    store = MemoryStore(pool, MemoryConfig(
        emb_base_url=cfg.emb_base_url,
        emb_api_key=cfg.emb_api_key,
        emb_model=cfg.emb_model,      # 这是 embedding 模型（例如 text-embedding-3-small）
        emb_dim=cfg.emb_dim,
        top_k=cfg.mem_top_k,
        min_sim=cfg.mem_min_sim,
    ))

    # 2) Runtime state
    state = RuntimeState(trigger_mode=cfg.trigger_mode)

    # 3) LLM client（聊天模型）
    if cfg.llm_base_url and cfg.llm_api_key and cfg.llm_model:
        llm = OpenAICompatLLMClient(
            base_url=cfg.llm_base_url,
            api_key=cfg.llm_api_key,
            model=cfg.llm_model,      # 这是聊天模型（例如 gpt-4o-mini）
            prefix=cfg.reply_prefix,
        )
    else:
        llm = DummyLLMClient(prefix=cfg.reply_prefix)

    print("[LLM] client type =", type(llm).__name__)
    async def on_event(ws, evt: Dict[str, Any]) -> None:
        try:
            if evt.get("post_type") != "message":
                return
            if evt.get("message_type") != "group":
                return

            group_id = int(evt.get("group_id", 0))
            if group_id == 0:
                return

            lock = state.lock_for_group(group_id)
            async with lock:
                # 注意：如果你的 on_message.py 已经改成需要 store，这里一定要传 store
                reply_text = await handle_group_message(ws, evt, state, llm, store)
                if reply_text:
                    await send_group_text(ws, group_id, reply_text)

        except Exception:
            import traceback
            traceback.print_exc()

    server = OneBotReverseWSServer(cfg.host, cfg.port, cfg.access_token)
    server.set_event_handler(on_event)

    print(f">>> OneBot reverse WS server listening on ws://{cfg.host}:{cfg.port}")

    try:
        await server.serve_forever()
    finally:
        # 释放资源（可选但推荐）
        if hasattr(llm, "aclose"):
            await llm.aclose()
        await store.aclose()
        await pool.close()


def run() -> None:
    asyncio.run(_amain())