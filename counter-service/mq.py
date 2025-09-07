from __future__ import annotations

import os
import json
from typing import Any, Awaitable, Callable

import aio_pika

AMQP_URL = os.getenv("RABBIT_URL", "amqp://guest:guest@rabbitmq:5672/")

_connection: aio_pika.RobustConnection | None = None


async def connect() -> aio_pika.RobustConnection:
    global _connection
    if _connection is None:
        _connection = await aio_pika.connect_robust(AMQP_URL)
    return _connection


async def start_message_consumer(handler: Callable[[dict[str, Any]], Awaitable[None]]):
    conn = await connect()
    ch = await conn.channel()
    exchange = await ch.declare_exchange("dialog", aio_pika.ExchangeType.TOPIC)
    queue = await ch.declare_queue("counters_unread", durable=True)
    await queue.bind(exchange, routing_key="message.created")

    async with queue.iterator() as it:
        async for message in it:
            async with message.process():
                data = json.loads(message.body.decode())
                await handler(data)

