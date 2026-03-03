from dataclasses import dataclass
import numpy as np
import httpx
import asyncpg


@dataclass(frozen=True)
class MemoryConfig:
    emb_base_url: str
    emb_api_key: str
    emb_model: str
    emb_dim: int
    top_k: int = 6
    min_sim: float = 0.25  # cosine similarity = 1 - cosine_distance


class MemoryStore:
    def __init__(self, pool: asyncpg.Pool, cfg: MemoryConfig):
        self.pool = pool
        base = cfg.emb_base_url.rstrip("/")
        self.emb_v1 = base if base.endswith("/v1") else base + "/v1"
        self.cfg = cfg
        self.http = httpx.AsyncClient(timeout=60)

    async def embed(self, text: str) -> np.ndarray:
        url = f"{self.emb_v1}/embeddings"
        headers = {"Authorization": f"Bearer {self.cfg.emb_api_key}"}
        payload = {"model": self.cfg.emb_model, "input": text}

        r = await self.http.post(url, headers=headers, json=payload)
        r.raise_for_status()
        data = r.json()
        vec = data["data"][0]["embedding"]
        # float32 更省空间
        v = np.array(vec, dtype=np.float32)
        if self.cfg.emb_dim and v.shape[0] != self.cfg.emb_dim:
            # 维度不符就直接报错，避免写入脏数据
            raise ValueError(f"Embedding dim mismatch: got {v.shape[0]} expected {self.cfg.emb_dim}")
        return v

    async def add_memory(self, group_id: int, user_id: int | None, role: str, content: str) -> None:
        v = await self.embed(content)
        async with self.pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO memories (group_id, user_id, role, content, embedding) VALUES ($1,$2,$3,$4,$5)",
                group_id, user_id, role, content, v
            )

    async def recall(self, group_id: int, query: str, top_k: int | None = None) -> list[str]:
        vq = await self.embed(query)
        k = top_k or self.cfg.top_k

        async with self.pool.acquire() as conn:
            # cosine distance: embedding <=> query_vec
            rows = await conn.fetch(
                """
                SELECT content,
                       1 - (embedding <=> $1) AS sim
                FROM memories
                WHERE group_id = $2
                ORDER BY embedding <=> $1
                LIMIT $3
                """,
                vq, group_id, k
            )

        out: list[str] = []
        for r in rows:
            if r["sim"] is None:
                continue
            if float(r["sim"]) >= self.cfg.min_sim:
                out.append(r["content"])
        return out

    async def aclose(self) -> None:
        await self.http.aclose()
