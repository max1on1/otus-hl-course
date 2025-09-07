from __future__ import annotations

import os
from typing import Optional

import redis.asyncio as redis


REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

_redis: redis.Redis | None = None


async def connect() -> None:
    global _redis
    if _redis is None:
        _redis = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)


async def disconnect() -> None:
    global _redis
    if _redis is not None:
        await _redis.aclose()
    _redis = None


def _key_unread(user_id: str, peer_id: str) -> str:
    return f"unread:{user_id}:{peer_id}"


def _key_unread_total(user_id: str) -> str:
    return f"unread_total:{user_id}"


async def inc_unread(user_id: str, peer_id: str, by: int = 1) -> None:
    if _redis is None:
        await connect()
    assert _redis is not None
    pipe = _redis.pipeline()
    pipe.incrby(_key_unread(user_id, peer_id), by)
    pipe.incrby(_key_unread_total(user_id), by)
    await pipe.execute()


async def get_unread_total(user_id: str) -> int:
    if _redis is None:
        await connect()
    assert _redis is not None
    val = await _redis.get(_key_unread_total(user_id))
    return int(val or 0)


async def get_unread(user_id: str, peer_id: str) -> int:
    if _redis is None:
        await connect()
    assert _redis is not None
    val = await _redis.get(_key_unread(user_id, peer_id))
    return int(val or 0)


async def reset_unread(user_id: str, peer_id: str) -> None:
    if _redis is None:
        await connect()
    assert _redis is not None
    # read current per-peer value, decrement total by that, and set to 0
    val = await get_unread(user_id, peer_id)
    pipe = _redis.pipeline()
    pipe.decrby(_key_unread_total(user_id), val)
    pipe.set(_key_unread(user_id, peer_id), 0)
    await pipe.execute()

