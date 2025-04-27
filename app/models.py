from pydantic import BaseModel
from typing import Optional
from datetime import date
from uuid import UUID

class UserCreate(BaseModel):
    first_name: str
    second_name: str
    birthdate: date  
    biography: str
    city: str
    password: str

class UserOut(BaseModel):
    id: UUID
    first_name: str
    second_name: str
    birthdate: date
    biography: str
    city: str

class UserLogin(BaseModel):
    id: UUID
    password: str