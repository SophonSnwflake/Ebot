from dataclasses import dataclass
import os

# 在当前目录（或父目录）找到 .env 文件并加载至环境变量
from dotenv import load_dotenv


@dataclass(frozen=True)
class Config:
    host: str
    port: int
    access_token: str
    trigger_mode: str  # "at" or "all"
    reply_prefix: str
    llm_base_url: str
    llm_api_key: str
    llm_model: str


def load_config() -> Config:
    load_dotenv()

    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8080"))
    access_token = os.getenv("ACCESS_TOKEN", "")
    trigger_mode = os.getenv("TRIGGER_MODE", "at").strip().lower()
    reply_prefix = os.getenv("REPLY_PREFIX", "")
    llm_base_url = os.getenv("LLM_BASE_URL", "").strip()
    llm_api_key  = os.getenv("LLM_API_KEY", "").strip()
    llm_model    = os.getenv("LLM_MODEL", "").strip()

    if trigger_mode not in ("at", "all"):
        trigger_mode = "at"

    return Config(
        host=host,
        port=port,
        access_token=access_token,
        trigger_mode=trigger_mode,
        reply_prefix=reply_prefix,
        llm_base_url=llm_base_url,
        llm_api_key=llm_api_key,
        llm_model=llm_model,
    )