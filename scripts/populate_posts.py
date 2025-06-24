import asyncio
import os
from uuid import uuid4
import asyncpg

LOREM = "Lorem ipsum dolor sit amet, consectetur adipiscing elit."

async def main():
    dsn = os.getenv("DB_DSN", "postgresql://postgres:postgres@localhost:5432/socialnetwork")
    conn = await asyncpg.connect(dsn)
    user_ids = await conn.fetch("SELECT id FROM users LIMIT 100")
    for row in user_ids:
        for _ in range(3):
            await conn.execute(
                "INSERT INTO posts(id, author_user_id, text) VALUES($1,$2,$3)",
                uuid4(),
                row["id"],
                LOREM,
            )
    await conn.close()

if __name__ == "__main__":
    asyncio.run(main())