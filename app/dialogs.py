from __future__ import annotations

from uuid import UUID, uuid4
from typing import List

import asyncpg

import dialog_db


async def send_message(sender_id: UUID, recipient_id: UUID, text: str) -> UUID:
    msg_id = uuid4()
    await dialog_db.execute(
        """
        INSERT INTO dialog_messages(id, sender_user_id, recipient_user_id, text)
        VALUES($1,$2,$3,$4)
        """,
        sender_id,
        recipient_id,
        msg_id,
        sender_id,
        recipient_id,
        text,
    )
    return msg_id


async def list_dialog(user1: UUID, user2: UUID) -> List[asyncpg.Record]:
    rows = await dialog_db.fetch(
        """
        SELECT id, sender_user_id, recipient_user_id, text, created_at
        FROM dialog_messages
        WHERE (sender_user_id=$1 AND recipient_user_id=$2)
           OR (sender_user_id=$2 AND recipient_user_id=$1)
        ORDER BY created_at
        """,
        user1,
        user2,
        user1,
        user2,
    )
    return rows