from __future__ import annotations

from datetime import date
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