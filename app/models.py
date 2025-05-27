from pydantic import BaseModel, Field
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
    firstName:  str = Field(..., alias="firstName")
    secondName: str = Field(..., alias="secondName")
    birthdate:  date
    biography:  Optional[str]
    city:       Optional[str]

    class Config:
        allow_population_by_field_name = True

class UserLogin(BaseModel):
    id: UUID
    password: str

class UserResponse(BaseModel):
    id: str
    first_name: str
    second_name: str
    birthdate: date
    biography: Optional[str]
    city: Optional[str]    