from __future__ import annotations

from contextlib import asynccontextmanager
from uuid import UUID

from fastapi import FastAPI, APIRouter, Depends, Path, Request, HTTPException
from jose import JWTError, jwt
import os
import asyncio

import cache
import mq


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


consumer_task: asyncio.Task | None = None


async def _on_message_created(evt: dict):
    # evt: { id, senderUserId, recipientUserId, createdAt }
    recipient = evt.get("recipientUserId")
    sender = evt.get("senderUserId")
    if recipient and sender:
        await cache.inc_unread(recipient, sender, 1)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global consumer_task
    await cache.connect()
    loop = asyncio.get_event_loop()
    consumer_task = loop.create_task(mq.start_message_consumer(_on_message_created))
    yield
    if consumer_task:
        consumer_task.cancel()
    await cache.disconnect()


app = FastAPI(title="Counter Service", version="1.0.0", lifespan=lifespan)


@app.middleware("http")
async def add_request_id_header(request: Request, call_next):
    req_id = request.headers.get("x-request-id")
    response = await call_next(request)
    if req_id:
        response.headers["x-request-id"] = req_id
    return response


router = APIRouter(prefix="/api/v1/counters")


@router.get("/unread/total")
async def unread_total(current_user: UUID = Depends(get_current_user_id)):
    total = await cache.get_unread_total(str(current_user))
    return {"total": total}


@router.get("/unread/{peer_id}")
async def unread_with_peer(
    peer_id: UUID = Path(...),
    current_user: UUID = Depends(get_current_user_id),
):
    cnt = await cache.get_unread(str(current_user), str(peer_id))
    return {"userId": str(peer_id), "unread": cnt}


@router.post("/unread/{peer_id}/reset", status_code=200)
async def reset_unread(
    peer_id: UUID = Path(...),
    current_user: UUID = Depends(get_current_user_id),
):
    await cache.reset_unread(str(current_user), str(peer_id))
    return {"ok": True}


app.include_router(router)

