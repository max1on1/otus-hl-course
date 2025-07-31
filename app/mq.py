import os
import json
import asyncio
from uuid import UUID
from typing import Any

import aio_pika

AMQP_URL = os.getenv("RABBIT_URL", "amqp://guest:guest@rabbitmq:5672/")

_connection: aio_pika.RobustConnection | None = None
_channel: aio_pika.Channel | None = None
_exchange: aio_pika.Exchange | None = None

async def connect() -> None:
    global _connection, _channel, _exchange
    if _connection is None:
        _connection = await aio_pika.connect_robust(AMQP_URL)
        _channel = await _connection.channel()
        _exchange = await _channel.declare_exchange(
            "feed", aio_pika.ExchangeType.DIRECT
        )
        queue = await _channel.declare_queue("feed_cache", durable=True)
        await queue.bind(_exchange, routing_key="#")

async def disconnect() -> None:
    global _connection, _channel, _exchange
    if _connection is not None:
        await _connection.close()
    _connection = _channel = _exchange = None

async def publish_post(follower_id: UUID, post: dict[str, Any]) -> None:
    if _connection is None:
        await connect()
    assert _channel is not None
    assert _exchange is not None
    msg = aio_pika.Message(
        body=json.dumps({"follower_id": str(follower_id), "post": post}).encode(),
    )
    await _exchange.publish(msg, routing_key=str(follower_id))

async def consume_cache(queue: aio_pika.Queue) -> None:
    async with queue.iterator() as it:
        async for message in it:
            async with message.process():
                import cache

                data = json.loads(message.body.decode())
                uid = UUID(data["follower_id"])
                await cache.push_post([uid], data["post"])

async def start_cache_worker() -> asyncio.Task:
    if _connection is None:
        await connect()
    assert _connection is not None
    ch = await _connection.channel()
    assert _exchange is not None
    queue = await ch.declare_queue("feed_cache", durable=True)
    await queue.bind(_exchange, routing_key="#")
    return asyncio.create_task(consume_cache(queue))

async def subscribe(user_id: UUID, websocket) -> asyncio.Task:
    if _connection is None:
        await connect()
    ch = await _connection.channel()
    assert _exchange is not None
    queue = await ch.declare_queue(exclusive=True)
    await queue.bind(_exchange, routing_key=str(user_id))

    async def _forward():
        async with queue.iterator() as it:
            async for message in it:
                async with message.process():
                    await websocket.send_text(message.body.decode())

    return asyncio.create_task(_forward())
