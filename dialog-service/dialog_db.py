from __future__ import annotations

import os
import hashlib
from uuid import UUID
from typing import List

import asyncpg


DSN_LIST: List[str] = [dsn.strip() for dsn in os.getenv("DIALOG_DB_DSNS", "").split(",") if dsn.strip()]

POOL_MIN_SIZE = int(os.getenv("POOL_MIN_SIZE", "1"))
POOL_MAX_SIZE = int(os.getenv("POOL_MAX_SIZE", "10"))
POOL_MAX_INACTIVE = float(os.getenv("POOL_MAX_INACTIVE", "300"))
STATEMENT_TIMEOUT_MS = int(os.getenv("STATEMENT_TIMEOUT_MS", "3000"))

_pools: List[asyncpg.Pool] = []

async def _init_conn(conn: asyncpg.Connection):
    await conn.execute(f"SET statement_timeout = {STATEMENT_TIMEOUT_MS}")

async def connect() -> None:
    global _pools
    if _pools:
        return
    if not DSN_LIST:
        raise RuntimeError("DIALOG_DB_DSNS is not configured")
    for dsn in DSN_LIST:
        pool = await asyncpg.create_pool(
            dsn,
            min_size=POOL_MIN_SIZE,
            max_size=POOL_MAX_SIZE,
            max_inactive_connection_lifetime=POOL_MAX_INACTIVE,
            init=_init_conn,
        )
        _pools.append(pool)

async def disconnect() -> None:
    global _pools
    for pool in _pools:
        await pool.close()
    _pools = []


def _shard_index(u1: UUID, u2: UUID) -> int:
    pair = (u1.hex if u1.int < u2.int else u2.hex) + (u2.hex if u1.int < u2.int else u1.hex)
    h = int(hashlib.sha1(pair.encode()).hexdigest(), 16)
    return h % max(len(_pools), 1)

async def _get_pool(u1: UUID, u2: UUID) -> asyncpg.Pool:
    if not _pools:
        await connect()
    return _pools[_shard_index(u1, u2)]

async def execute(sql: str, u1: UUID, u2: UUID, *args):
    pool = await _get_pool(u1, u2)
    async with pool.acquire() as conn:
        return await conn.execute(sql, *args)

async def fetch(sql: str, u1: UUID, u2: UUID, *args):
    pool = await _get_pool(u1, u2)
    async with pool.acquire() as conn:
        return await conn.fetch(sql, *args)

