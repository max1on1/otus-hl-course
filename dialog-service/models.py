from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field
from uuid import UUID


class DialogMessageIn(BaseModel):
    text: str


class DialogMessage(BaseModel):
    id: UUID
    sender_user_id: UUID = Field(..., alias="senderUserId")
    recipient_user_id: UUID = Field(..., alias="recipientUserId")
    text: str
    created_at: datetime = Field(..., alias="createdAt")

    model_config = {
        "populate_by_name": True
    }

