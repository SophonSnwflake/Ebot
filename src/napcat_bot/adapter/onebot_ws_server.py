import asyncio
import json
from typing import Any, Awaitable, Callable, Dict, Optional

import websockets

from ..utils.log import setup_logger

logger = setup_logger("napcat_bot.ws")

EventHandler = Callable[[Any, Dict[str, Any]], Awaitable[None]]


def _get_header(ws: Any, name: str, default: str = "") -> str:
    """
    兼容不同 websockets 版本的取 header 方法：
    - 旧版：ws.request_headers
    - 新版：ws.request.headers
    """
    # websockets <= 11 常见
    rh = getattr(ws, "request_headers", None)
    if rh is not None:
        try:
            return rh.get(name, default)
        except Exception:
            pass

    # websockets >= 12 常见：ServerConnection.request.headers
    req = getattr(ws, "request", None)
    headers = getattr(req, "headers", None)
    if headers is not None:
        try:
            return headers.get(name, default)
        except Exception:
            pass

    return default


class OneBotReverseWSServer:
    def __init__(self, host: str, port: int, access_token: str = "") -> None:
        self.host = host
        self.port = port
        self.access_token = access_token
        self._handler: Optional[EventHandler] = None

    def set_event_handler(self, handler: EventHandler) -> None:
        self._handler = handler

    async def _auth_or_close(self, ws: Any) -> bool:
        # access_token 为空：不做鉴权（方便你本地快速跑通）
        if not self.access_token:
            return True

        auth = _get_header(ws, "Authorization", "")
        expected = f"Bearer {self.access_token}"

        if auth != expected:
            logger.warning("Rejected connection. Authorization=%s", auth)
            await ws.close(code=1008, reason="Unauthorized")
            return False

        return True

    async def _handle_conn(self, ws: Any) -> None:
        if not await self._auth_or_close(ws):
            return

        remote = getattr(ws, "remote_address", None)
        logger.info("Connected: %s", remote)

        try:
            async for raw in ws:
                try:
                    data = json.loads(raw)
                except Exception:
                    logger.warning("Non-JSON frame: %r", raw)
                    continue

                # OneBot event 通常有 post_type
                if isinstance(data, dict) and "post_type" in data:
                    if self._handler:
                        await self._handler(ws, data)
                else:
                    # 可能是 action 响应（带 echo）
                    echo = data.get("echo") if isinstance(data, dict) else None
                    if echo:
                        logger.info("Action response echo=%s data=%s", echo, data)

        except Exception as e:
            # ConnectionClosed 等各版本异常类不同，这里统一兜底
            logger.info("Disconnected (%s): %s", type(e).__name__, remote)

    async def serve_forever(self) -> None:
        logger.info("OneBot reverse WS server listening on ws://%s:%d", self.host, self.port)
        async with websockets.serve(self._handle_conn, self.host, self.port):
            await asyncio.Future()