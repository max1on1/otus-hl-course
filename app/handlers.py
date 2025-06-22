from __future__ import annotations

from datetime import datetime, timedelta
from typing import List
from uuid import UUID, uuid4

import os

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Path,
    Query,
    
)
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.hash import bcrypt

import db

import cache
from models import (
    UserLoginIn,
    UserOut,
    UserRegisterIn,
    PostCreateIn,
    PostUpdateIn,
    PostOut,
)
router = APIRouter()


FEED_CACHE_SIZE = cache.FEED_SIZE


async def _followers(user_id: UUID) -> List[UUID]:
    rows = await db.fetch(
        "SELECT user_id FROM friends WHERE friend_id=$1",
        user_id,
    )
    return [r["user_id"] for r in rows]


async def _load_feed(user_id: UUID) -> List[dict]:
    rows = await db.fetch(
        """
        SELECT p.id, p.text, p.author_user_id
        FROM friends f
        JOIN posts p ON p.author_user_id = f.friend_id
        WHERE f.user_id = $1
        ORDER BY p.created_at DESC
        LIMIT $2
        """,
        user_id,
        FEED_CACHE_SIZE,
    )
    posts = [dict(r) for r in rows]
    await cache.save_feed(user_id, posts)
    return posts


async def _push_to_feeds(post: dict) -> None:
    followers = await _followers(post["author_user_id"])
    await cache.push_post(followers, post)
# --------------
# JWT helpers
# --------------
SECRET_KEY = os.getenv("SECRET_KEY", "dev‑secret‑please‑override")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

auth_scheme = HTTPBearer(auto_error=False)


def create_token(user_id: UUID) -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode({"sub": str(user_id), "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(auth_scheme),
) -> UUID:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Missing Bearer token")
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return UUID(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid token")

# ------------
# Users
# ------------

@router.post("/user/register", status_code=200)
async def register(user: UserRegisterIn):
    user_id = uuid4()
    pwd_hash = bcrypt.hash(user.password)
    try:
        await db.execute(
            """
            INSERT INTO users(id, first_name, second_name, birthdate, biography, city, password_hash)
            VALUES($1,$2,$3,$4,$5,$6,$7)
            """,
            user_id,
            user.first_name,
            user.second_name,
            user.birthdate,
            user.biography,
            user.city,
            pwd_hash,
        )
    except Exception:
        raise HTTPException(status_code=500, detail="Could not create user")

    return {"user_id": str(user_id)}


@router.post("/login", status_code=200)
async def login(payload: UserLoginIn):
    row = await db.fetchrow("SELECT password_hash FROM users WHERE id=$1", payload.id)
    if row is None:
        raise HTTPException(status_code=404, detail="User not found")
    if not bcrypt.verify(payload.password, row["password_hash"]):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    return {"token": create_token(payload.id)}


@router.get("/user/get/{id}", response_model=UserOut)
async def get_user(id: UUID = Path(...)):
    row = await db.fetchrow(
        """
        SELECT id,
               first_name  AS "firstName",
               second_name AS "secondName",
               birthdate,
               biography,
               city
        FROM users WHERE id=$1
        """,
        id,
    )
    if row is None:
        raise HTTPException(status_code=404, detail="User not found")
    return UserOut(**dict(row))


@router.get("/user/search", response_model=List[UserOut])
async def search_users(
    first_name: str = Query(..., alias="firstName"),
    second_name: str = Query(..., alias="secondName"),
):
    rows = await db.fetch(
        """
        SELECT id,
               first_name  AS "firstName",
               second_name AS "secondName",
               birthdate,
               biography,
               city
        FROM users
        WHERE first_name  ILIKE $1
          AND second_name ILIKE $2
        ORDER BY id
        """,
        f"{first_name}%",
        f"{second_name}%",
    )
    return [UserOut(**dict(r)) for r in rows]


# ------------
# Friendships
# ------------
@router.put("/friend/set/{user_id}")
async def add_friend(
    user_id: UUID = Path(..., description="ID пользователя, которого добавляем в друзья"),
    current_user: UUID = Depends(get_current_user_id),
):
    if user_id == current_user:
        raise HTTPException(status_code=400, detail="Cannot add yourself")
    await db.execute(
        """
        INSERT INTO friends(user_id, friend_id)
        VALUES($1,$2) ON CONFLICT DO NOTHING
        """,
        current_user,
        user_id,
    )
    await _load_feed(current_user)
    return {"ok": True}


@router.put("/friend/delete/{user_id}")
async def remove_friend(
    user_id: UUID = Path(...),
    current_user: UUID = Depends(get_current_user_id),
):
    await db.execute(
        "DELETE FROM friends WHERE user_id=$1 AND friend_id=$2",
        current_user,
        user_id,
    )
    await _load_feed(current_user)
    return {"ok": True}

@router.get("/friend/list", response_model=List[UserOut])
async def list_friends(current_user: UUID = Depends(get_current_user_id)):
    rows = await db.fetch(
        '''
        SELECT u.id,
               u.first_name  AS "firstName",
               u.second_name AS "secondName",
               u.birthdate,
               u.biography,
               u.city
        FROM friends f
        JOIN users u ON u.id = f.friend_id
        WHERE f.user_id = $1
        ORDER BY u.first_name, u.second_name
        ''',
        current_user,
    )
    return [UserOut(**dict(r)) for r in rows]

# ------------
# Posts
# ------------

@router.post("/post/create", response_model=UUID)
async def create_post(
    payload: PostCreateIn,
    current_user: UUID = Depends(get_current_user_id),
):
    post_id = uuid4()
    await db.execute(
        """
        INSERT INTO posts(id, author_user_id, text)
        VALUES($1,$2,$3)
        """,
        post_id,
        current_user,
        payload.text,
    )
    post = {"id": post_id, "text": payload.text, "author_user_id": current_user}
    await _push_to_feeds(post)
    return post_id


@router.put("/post/update")
async def update_post(
    payload: PostUpdateIn,
    current_user: UUID = Depends(get_current_user_id),
):
    row = await db.fetchrow(
        "SELECT author_user_id FROM posts WHERE id=$1",
        payload.id,
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Post not found")
    if row["author_user_id"] != current_user:
        raise HTTPException(status_code=401, detail="Not allowed")
    await db.execute(
        "UPDATE posts SET text=$2, updated_at=now() WHERE id=$1",
        payload.id,
        payload.text,
    )
    followers = await _followers(current_user)
    for uid in followers:
        await _load_feed(uid)
    return {"ok": True}


@router.put("/post/delete/{id}")
async def delete_post(
    id: UUID = Path(...),
    current_user: UUID = Depends(get_current_user_id),
):
    row = await db.fetchrow(
        "SELECT author_user_id FROM posts WHERE id=$1",
        id,
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Post not found")
    if row["author_user_id"] != current_user:
        raise HTTPException(status_code=401, detail="Not allowed")
    await db.execute("DELETE FROM posts WHERE id=$1", id)
    followers = await _followers(current_user)
    for uid in followers:
        await _load_feed(uid)
    return {"ok": True}


@router.get("/post/get/{id}", response_model=PostOut)
async def get_post(id: UUID = Path(...)):
    row = await db.fetchrow(
        "SELECT id, text, author_user_id FROM posts WHERE id=$1",
        id,
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Post not found")
    return PostOut(**dict(row))


@router.get("/post/feed", response_model=List[PostOut])
async def feed(
    offset: int = Query(0, ge=0),
    limit: int = Query(10, ge=1),
    current_user: UUID = Depends(get_current_user_id),
):
    if not await cache.has_feed(current_user):
        await _load_feed(current_user)
    posts = await cache.get_feed(current_user, offset, limit)
    return [PostOut(**p) for p in posts]