from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

import db
import cache
import mq
from handlers import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.connect()
    await cache.connect()
    await mq.connect()
    worker = await mq.start_cache_worker()    
    yield
    worker.cancel()
    await mq.disconnect()    
    await cache.disconnect()
    await db.disconnect()


app = FastAPI(
    title="OTUS Highload Architect",
    version="1.2.0",
    lifespan=lifespan,
)

app.include_router(router)

# x-request-id propagation
from starlette.requests import Request
from starlette.responses import Response
import uuid

@app.middleware("http")
async def add_request_id_header(request: Request, call_next):
    req_id = request.headers.get("x-request-id") or str(uuid.uuid4())
    response: Response = await call_next(request)
    response.headers["x-request-id"] = req_id
    return response
