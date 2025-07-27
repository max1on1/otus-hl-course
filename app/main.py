from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

import db
import cache
import dialog_db
import mq
from handlers import router
from websocket_router import ws_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.connect()
    await cache.connect()
    await dialog_db.connect()
    await mq.connect()
    worker = await mq.start_cache_worker()    
    yield
    worker.cancel()
    await mq.disconnect()    
    await cache.disconnect()
    await dialog_db.disconnect()
    await db.disconnect()


app = FastAPI(
    title="OTUS Highload Architect",
    version="1.2.0",
    lifespan=lifespan,
)

app.include_router(router)
app.include_router(ws_router)