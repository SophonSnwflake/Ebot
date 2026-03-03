from dataclasses import dataclass
import os

from dotenv import load_dotenv


@dataclass(frozen=True)
class Config:
    # Bot / NapCat WS server
    host: str
    port: int
    access_token: str
    trigger_mode: str   # "at" or "all"
    reply_prefix: str

    # Chat LLM (OpenAI-compatible / httpx)
    llm_base_url: str
    llm_api_key: str
    llm_model: str

    # PostgreSQL + pgvector
    pg_dsn: str

    # Embedding model (for memory/RAG)
    emb_base_url: str
    emb_api_key: str
    emb_model: str
    emb_dim: int

    # Memory retrieval tuning
    mem_top_k: int
    mem_min_sim: float


def _get_int(name: str, default: int) -> int:
    raw = os.getenv(name, str(default)).strip()
    try:
        return int(raw)
    except ValueError:
        return default


def _get_float(name: str, default: float) -> float:
    raw = os.getenv(name, str(default)).strip()
    try:
        return float(raw)
    except ValueError:
        return default


def load_config() -> Config:
    # 默认读取项目根目录 .env（不是 .env.example）
    load_dotenv()

    # 基础网络配置
    host = os.getenv("HOST", "127.0.0.1").strip()
    port = _get_int("PORT", 8080)
    access_token = os.getenv("ACCESS_TOKEN", "").strip()

    # 触发模式
    trigger_mode = os.getenv("TRIGGER_MODE", "at").strip().lower()
    if trigger_mode not in ("at", "all"):
        trigger_mode = "at"

    reply_prefix = os.getenv("REPLY_PREFIX", "")

    # 聊天 LLM（你回复用的模型）
    llm_base_url = os.getenv("LLM_BASE_URL", "").strip()
    llm_api_key = os.getenv("LLM_API_KEY", "").strip()
    llm_model = os.getenv("LLM_MODEL", "").strip()

    # PostgreSQL
    pg_dsn = os.getenv("PG_DSN", "").strip()
    # 你也可以给默认值（本地开发常用）
    if not pg_dsn:
        pg_dsn = "postgresql://postgres:postgres@127.0.0.1:5432/qqbot"

    # Embedding（记忆向量用）
    emb_base_url = os.getenv("EMB_BASE_URL", "").strip()
    emb_api_key = os.getenv("EMB_API_KEY", "").strip()
    emb_model = os.getenv("EMB_MODEL", "").strip()
    emb_dim = _get_int("EMB_DIM", 1536)

    # 如果你希望 embedding 默认复用 LLM 的接口/key（很多中转站是同一个）
    if not emb_base_url:
        emb_base_url = llm_base_url
    if not emb_api_key:
        emb_api_key = llm_api_key

    # 记忆检索参数
    mem_top_k = _get_int("MEM_TOP_K", 6)
    mem_min_sim = _get_float("MEM_MIN_SIM", 0.25)

    # 简单兜底（避免异常值）
    if mem_top_k <= 0:
        mem_top_k = 6
    if mem_min_sim < -1 or mem_min_sim > 1:
        mem_min_sim = 0.25

    return Config(
        host=host,
        port=port,
        access_token=access_token,
        trigger_mode=trigger_mode,
        reply_prefix=reply_prefix,

        llm_base_url=llm_base_url,
        llm_api_key=llm_api_key,
        llm_model=llm_model,

        pg_dsn=pg_dsn,

        emb_base_url=emb_base_url,
        emb_api_key=emb_api_key,
        emb_model=emb_model,
        emb_dim=emb_dim,

        mem_top_k=mem_top_k,
        mem_min_sim=mem_min_sim,
    )