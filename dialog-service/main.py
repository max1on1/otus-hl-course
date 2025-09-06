from __future__ import annotations

from typing import List
from uuid import UUID, uuid4

from fastapi import FastAPI, APIRouter, Depends, Path, HTTPException, Request
from jose import JWTError, jwt
import os

from models import DialogMessageIn, DialogMessage


SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
ALGORITHM = "HS256"


def get_current_user_id(request: Request) -> UUID:
    auth = request.headers.get("authorization")
    if not auth or not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer token")
    token = auth.split()[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return UUID(payload["sub"])  # type: ignore[index]
    except (JWTError, KeyError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid token")


from contextlib import asynccontextmanager
import dialog_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Lazy DB init happens on first request via dialog_db._get_pool
    yield


app = FastAPI(
    title="Dialog Service",
    version="1.0.0",
    lifespan=lifespan,
)


@app.middleware("http")
async def add_request_id_header(request: Request, call_next):
    req_id = request.headers.get("x-request-id")
    response = await call_next(request)
    if req_id:
        response.headers["x-request-id"] = req_id
    return response


router = APIRouter(prefix="/api/v1")


@router.post("/dialog/{user_id}/send", status_code=200)
async def dialog_send(
    payload: DialogMessageIn,
    user_id: UUID = Path(...),
    current_user: UUID = Depends(get_current_user_id),
):
    msg_id = uuid4()
    await dialog_db.execute(
        """
        INSERT INTO dialog_messages(id, sender_user_id, recipient_user_id, text)
        VALUES($1,$2,$3,$4)
        """,
        current_user,
        user_id,
        msg_id,
        current_user,
        user_id,
        payload.text,
    )
    return {"ok": True, "id": str(msg_id)}


@router.get("/dialog/{user_id}/list", response_model=List[DialogMessage])
async def dialog_list(
    user_id: UUID = Path(...),
    current_user: UUID = Depends(get_current_user_id),
):
    rows = await dialog_db.fetch(
        """
        SELECT id, sender_user_id AS "senderUserId", recipient_user_id AS "recipientUserId", text, created_at AS "createdAt"
        FROM dialog_messages
        WHERE (sender_user_id=$1 AND recipient_user_id=$2)
           OR (sender_user_id=$2 AND recipient_user_id=$1)
        ORDER BY created_at
        """,
        current_user,
        user_id,
        current_user,
        user_id,
    )
    return [DialogMessage(**dict(r)) for r in rows]


app.include_router(router)
