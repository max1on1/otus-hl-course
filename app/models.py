from __future__ import annotations

from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


#  входящие модели
class UserRegisterIn(BaseModel):
    first_name: str = Field(..., alias="firstName")
    second_name: str = Field(..., alias="secondName")
    birthdate: date
    biography: Optional[str] = None
    city: Optional[str] = None
    password: str

    class Config:
        allow_population_by_field_name = True


class UserLoginIn(BaseModel):
    id: UUID
    password: str


# исходящие модели
class UserOut(BaseModel):
    """Публичный профиль пользователя (response model)."""

    id: UUID
    first_name: str = Field(..., alias="firstName")
    second_name: str = Field(..., alias="secondName")
    birthdate: date
    biography: Optional[str] = None
    city: Optional[str] = None

    class Config:
        allow_population_by_field_name = True

# -----------------
# Posts models
# -----------------

class PostCreateIn(BaseModel):
    text: str


class PostUpdateIn(BaseModel):
    id: UUID
    text: str


class PostOut(BaseModel):
    id: UUID
    text: str
    author_user_id: UUID = Field(..., alias="authorUserId")

    model_config = {
        "populate_by_name": True  }
# -----------------
# Dialog models
# -----------------

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