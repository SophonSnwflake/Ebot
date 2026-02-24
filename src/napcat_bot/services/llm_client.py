from dataclasses import dataclass
import httpx


@dataclass
class LLMRequest:
    user_id: int
    group_id: int
    text: str


class LLMClient:
    async def generate(self, req: LLMRequest) -> str:
        raise NotImplementedError


class OpenAICompatLLMClient(LLMClient):
    """
    用 httpx 直连 OpenAI-compatible API：
    - POST {base_url}/chat/completions
    - Header: Authorization: Bearer <api_key>
    - Body: {model, messages, temperature, ...}
    """

    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        prefix: str = "",
        temperature: float = 0.7,
        timeout_s: float = 60.0,
    ):
        base_url = base_url.rstrip("/")
        # 兼容两种写法：
        # 1) base_url="https://api.xxx.com/v1"
        # 2) base_url="https://api.xxx.com"
        if base_url.endswith("/v1"):
            self.base_v1 = base_url
        else:
            self.base_v1 = base_url + "/v1"

        self.api_key = api_key
        self.model = model
        self.prefix = prefix
        self.temperature = temperature
        self.client = httpx.AsyncClient(timeout=timeout_s)

    async def generate(self, req: LLMRequest) -> str:
        url = f"{self.base_v1}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "你的名字叫Ebot，也叫小e，你是聊天机器人。"},
                {"role": "user", "content": req.text},
            ],
            "temperature": self.temperature,
        }

        resp = await self.client.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()

        # OpenAI-compatible: choices[0].message.content
        text = (data.get("choices", [{}])[0].get("message", {}) or {}).get("content", "") or ""
        return f"{self.prefix}{text}" if self.prefix else text

    async def aclose(self) -> None:
        await self.client.aclose()


class DummyLLMClient(LLMClient):
    def __init__(self, prefix: str = "") -> None:
        self.prefix = prefix

    async def generate(self, req: LLMRequest) -> str:
        base = f"（LLM未接入）你说的是：{req.text}"
        return f"{self.prefix}{base}" if self.prefix else base