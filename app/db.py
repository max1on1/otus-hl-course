from __future__ import annotations

import os
import random
from typing import Optional, Sequence, List

import asyncpg

# ────────────────── env / config ──────────────────
WRITE_DSN = os.getenv("DB_WRITE_DSN") or os.getenv(
    "DATABASE_URL",
    f"postgresql://{os.getenv('DB_USER', 'postgres')}:{os.getenv('DB_PASSWORD', 'postgres')}@"
    f"{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '5432')}/"
    f"{os.getenv('DB_NAME', 'socialnetwork')}",
)

READ_DSNS: List[str] = [dsn.strip() for dsn in os.getenv("DB_READ_DSNS", "").split(",") if dsn.strip()]

POOL_MIN_SIZE = int(os.getenv("POOL_MIN_SIZE", 1))
POOL_MAX_SIZE = int(os.getenv("POOL_MAX_SIZE", 10))
POOL_MAX_INACTIVE = float(os.getenv("POOL_MAX_INACTIVE", 300))  # sec
POOL_ACQUIRE_TIMEOUT = float(os.getenv("POOL_ACQUIRE_TIMEOUT", 10))  # sec
STATEMENT_TIMEOUT_MS = int(os.getenv("STATEMENT_TIMEOUT_MS", 5000))

# ────pools ───────---
_write_pool: Optional[asyncpg.Pool] = None
_read_pools: List[asyncpg.Pool] = []


# ────lifecycle ──────
async def startup() -> None:  # called from FastAPI startup
    """Initialize pools (idempotent)."""
    global _write_pool, _read_pools
    if _write_pool is None:
        _write_pool = await asyncpg.create_pool(
            WRITE_DSN, min_size=POOL_MIN_SIZE, max_size=POOL_MAX_SIZE
        )
        _read_pools = [
            await asyncpg.create_pool(dsn, min_size=POOL_MIN_SIZE, max_size=POOL_MAX_SIZE)
            for dsn in READ_DSNS
        ]


async def shutdown() -> None:  # called from FastAPI shutdown
    """Close all pools cleanly."""
    global _write_pool, _read_pools
    if _write_pool is not None:
        await _write_pool.close()
        _write_pool = None
    for pool in _read_pools:
        await pool.close()
    _read_pools = []


# ────────────────── helpers ──────────────────
async def _init_conn(conn: asyncpg.Connection):
    """Инициализация каждой новой сессии (statement_timeout)."""
    await conn.execute(f"SET statement_timeout = {STATEMENT_TIMEOUT_MS}")


async def _create_pool(dsn: str) -> asyncpg.Pool:
    return await asyncpg.create_pool(
        dsn,
        min_size=POOL_MIN_SIZE,
        max_size=POOL_MAX_SIZE,
        max_inactive_connection_lifetime=POOL_MAX_INACTIVE,
        init=_init_conn,
    )


async def _get_pool(readonly: bool = False) -> asyncpg.Pool:
    if _write_pool is None:
        await startup()  # lazy init
    if readonly and _read_pools:
        return random.choice(_read_pools)
    return _write_pool  # type: ignore[return-value]


# ────────────────── public API ──────────────────
async def fetch(sql: str, *args, readonly: bool = False):
    pool = await _get_pool(readonly)
    async with pool.acquire() as conn:
        return await conn.fetch(sql, *args)


async def fetchrow(sql: str, *args, readonly: bool = False):
    pool = await _get_pool(readonly)
    async with pool.acquire() as conn:
        return await conn.fetchrow(sql, *args)


async def execute(sql: str, *args, readonly: bool = False):
    pool = await _get_pool(readonly)
    async with pool.acquire() as conn:
        return await conn.execute(sql, *args)

async def connect() -> None:      
    await startup()               

async def disconnect() -> None:   
    await shutdown()             
