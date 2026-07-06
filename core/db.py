import asyncpg
import os
from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file

DB_URL = os.getenv("DATABASE_URL")  # postgresql://user:pass@host:port/dbname

pool: asyncpg.Pool | None = None

async def init_db():
    global pool
    pool = await asyncpg.create_pool(DB_URL)
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS chat_history (
                id SERIAL PRIMARY KEY,
                chat_id BIGINT NOT NULL,
                role TEXT NOT NULL,        -- 'user' or 'assistant'
                content TEXT NOT NULL,
                created_at TIMESTAMPTZ DEFAULT NOW()
            );
        """)
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_chat_id_time
            ON chat_history (chat_id, created_at);
        """)

async def save_message(chat_id: int, role: str, content: str):
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO chat_history (chat_id, role, content) VALUES ($1, $2, $3)",
            chat_id, role, content
        )

async def get_history(chat_id: int, limit: int = 10):
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT role, content FROM chat_history
            WHERE chat_id = $1
            ORDER BY created_at DESC
            LIMIT $2
            """,
            chat_id, limit
        )
    return [dict(r) for r in reversed(rows)]  # oldest -> newest

async def clear_history(chat_id: int):
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM chat_history WHERE chat_id = $1", chat_id)