import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/socialnetwork")

SQL = """
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY,
    first_name TEXT NOT NULL,
    second_name TEXT NOT NULL,
    birthdate DATE NOT NULL,
    biography TEXT,
    city TEXT,
    password_hash TEXT NOT NULL
);
"""
async def create_tables():
    conn = await asyncpg.connect(DB_URL)
    await conn.execute(SQL)
    await conn.close()

if __name__ == "__main__":
    asyncio.run(create_tables())