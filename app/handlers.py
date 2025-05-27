from fastapi import APIRouter, HTTPException, Query
import db
from models import UserCreate, UserOut, UserLogin, UserResponse
import bcrypt
import uuid
from uuid import UUID
from typing import List


router = APIRouter()

@router.post("/user/register")
async def register(user: UserCreate):
    conn = await db.get_db_connection()
    hashed_pw = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    user_id = str(uuid.uuid4())
    try:
        await conn.execute('''
            INSERT INTO users (id, first_name, second_name, birthdate, biography, city, password_hash)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
        ''', user_id, user.first_name, user.second_name, user.birthdate, user.biography, user.city, hashed_pw)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await conn.close()
    return {"user_id": user_id}

@router.post("/login")
async def login(user: UserLogin):
    conn = await db.get_db_connection()
    row = await conn.fetchrow('SELECT password_hash FROM users WHERE id = $1', user.id)
    await conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    if not bcrypt.checkpw(user.password.encode('utf-8'), row['password_hash'].encode('utf-8')):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    # В реальности сюда нужен JWT токен, пока вернём фейковый токен
    return {"token": str(uuid.uuid4())}

@router.get("/user/get/{id}", response_model=UserOut)
async def get_user(id: UUID):
    conn = await db.get_db_connection()
    row = await conn.fetchrow(
            '''
            SELECT
                id,
                first_name  AS "firstName",
                second_name AS "secondName",
                birthdate,
                biography,
                city
            FROM users
            WHERE id = $1
            ''',
            id
        )
    await conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    return dict(row)

@router.get("/user/search", response_model=List[UserOut])
async def search_users(
    firstName:  str = Query(..., alias="firstName"),
    secondName: str = Query(..., alias="secondName"),
):
    conn = await db.get_db_connection()
    try:
        rows = await conn.fetch(
            '''
            SELECT
              id,
              first_name  AS "firstName",
              second_name AS "secondName",
              birthdate,
              biography,
              city
            FROM users
            WHERE first_name  LIKE $1
              AND second_name LIKE $2
            ORDER BY id
            ''',
            f"{firstName}%",
            f"{secondName}%",
        )
    finally:
        await conn.close()

    return [dict(r) for r in rows]