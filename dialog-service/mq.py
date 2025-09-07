from __future__ import annotations

import os
import json
from datetime import datetime

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
        _exchange = await _channel.declare_exchange("dialog", aio_pika.ExchangeType.TOPIC)


async def disconnect() -> None:
    global _connection, _channel, _exchange
    if _connection is not None:
        await _connection.close()
    _connection = _channel = _exchange = None


async def publish_message_created(
    message_id: str,
    sender_id: str,
    recipient_id: str,
    created_at: datetime,
) -> None:
    if _connection is None:
        await connect()
    assert _exchange is not None
    payload = {
        "id": message_id,
        "senderUserId": sender_id,
        "recipientUserId": recipient_id,
        "createdAt": created_at.isoformat(),
    }
    msg = aio_pika.Message(body=json.dumps(payload).encode())
    await _exchange.publish(msg, routing_key="message.created")

