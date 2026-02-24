import re
from typing import Any, Dict


_AT_RE = re.compile(r"\[CQ:at,qq=(\d+)\]")


def extract_plain_text(evt: Dict[str, Any]) -> str:
    # OneBot v11 里常见字段：raw_message 是字符串，message 可能是字符串或数组
    raw = evt.get("raw_message")
    if isinstance(raw, str):
        return raw.strip()
    msg = evt.get("message")
    if isinstance(msg, str):
        return msg.strip()
    # 如果是数组段格式，这里先简单拼一下
    if isinstance(msg, list):
        parts = []
        for seg in msg:
            if isinstance(seg, dict):
                if seg.get("type") == "text":
                    parts.append(seg.get("data", {}).get("text", ""))
        return "".join(parts).strip()
    return ""


def is_at_me(evt: Dict[str, Any]) -> bool:
    """
    判断消息里是否 @ 机器人自己：
    - OneBot v11 事件通常有 self_id
    - raw_message 里会出现 [CQ:at,qq=xxxx]
    """
    self_id = str(evt.get("self_id", ""))
    raw = evt.get("raw_message", "")
    if not (self_id and isinstance(raw, str)):
        return False

    for m in _AT_RE.finditer(raw):
        if m.group(1) == self_id:
            return True
    return False


def strip_at_me(text: str) -> str:
    # 把所有 at 段去掉，避免 LLM 看到一堆 CQ 码
    text = _AT_RE.sub("", text)
    return text.strip()