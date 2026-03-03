-- 初始化数据库脚本
-- 执行命令（Powershell）：Get-Content -Raw .\scripts\init_db.sql | docker exec -i qqbot-pg psql -U postgres -d qqbot

-- 启用扩展
CREATE EXTENSION IF NOT EXISTS vector;

-- 原始消息
CREATE TABLE IF NOT EXISTS chat_messages (
  id          BIGSERIAL PRIMARY KEY, --自增主键
  group_id    BIGINT NOT NULL,       --群号
  user_id     BIGINT,                --用户ID
  role        TEXT NOT NULL,         --人还是机器人？ 
  content     TEXT NOT NULL,         --消息内容
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 记忆向量表(1536维)
CREATE TABLE IF NOT EXISTS memories (
  id          BIGSERIAL PRIMARY KEY,
  group_id    BIGINT NOT NULL,
  user_id     BIGINT,
  role        TEXT NOT NULL,          
  content     TEXT NOT NULL,
  embedding   VECTOR(1536) NOT NULL,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 常用过滤
CREATE INDEX IF NOT EXISTS idx_memories_group_time ON memories (group_id, created_at DESC);

-- 向量索引（HNSW + cosine）
CREATE INDEX IF NOT EXISTS idx_memories_hnsw
ON memories USING hnsw (embedding vector_cosine_ops);