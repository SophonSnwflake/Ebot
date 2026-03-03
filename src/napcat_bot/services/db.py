import asyncpg
from pgvector.asyncpg import register_vector


async def create_pg_pool(dsn: str) -> asyncpg.Pool:
    async def init(conn: asyncpg.Connection):
        # 注意：CREATE EXTENSION 需要足够权限，建议你已手动执行过 init_db.sql
        await register_vector(conn)

    return await asyncpg.create_pool(dsn=dsn, min_size=1, max_size=5, init=init)