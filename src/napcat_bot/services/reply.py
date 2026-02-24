import json
from typing import Any, Dict, Optional


async def send_group_text(ws, group_id: int, text: str, echo: Optional[str] = None) -> None:
    payload: Dict[str, Any] = {
        "action": "send_group_msg",
        "params": {"group_id": group_id, "message": text},
    }
    if echo is not None:
        payload["echo"] = echo
    await ws.send(json.dumps(payload, ensure_ascii=False))