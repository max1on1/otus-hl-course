from __future__ import annotations

import os
import json
from uuid import UUID
from typing import List

import redis.asyncio as aioredis

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

FEED_SIZE = int(os.getenv("FEED_CACHE_SIZE", 1000))
FEED_PREFIX = "feed:"

_client: aioredis.Redis | None = None


async def connect() -> None:
    global _client
    if _client is None:
        _client = aioredis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)


async def disconnect() -> None:
    global _client
    if _client is not None:
        await _client.close()
        _client = None


async def has_feed(user_id: UUID) -> bool:
    await connect()
    assert _client is not None
    return bool(await _client.exists(f"{FEED_PREFIX}{user_id}"))


async def get_feed(user_id: UUID, offset: int, limit: int) -> List[dict]:
    await connect()
    assert _client is not None
    raw = await _client.lrange(f"{FEED_PREFIX}{user_id}", offset, offset + limit - 1)
    return [json.loads(item) for item in raw]


async def save_feed(user_id: UUID, posts: List[dict]) -> None:
    await connect()
    assert _client is not None
    key = f"{FEED_PREFIX}{user_id}"
    await _client.delete(key)
    if posts:
        data = [json.dumps({"id": str(p["id"]), "text": p["text"], "author_user_id": str(p["author_user_id"])}) for p in posts]
        await _client.rpush(key, *data)
        await _client.ltrim(key, -FEED_SIZE, -1)


async def push_post(follower_ids: List[UUID], post: dict) -> None:
    await connect()
    assert _client is not None
    data = json.dumps({"id": str(post["id"]), "text": post["text"], "author_user_id": str(post["author_user_id"])})
    pipe = _client.pipeline()
    for uid in follower_ids:
        key = f"{FEED_PREFIX}{uid}"
        pipe.lpush(key, data)
        pipe.ltrim(key, 0, FEED_SIZE - 1)
    await pipe.execute()