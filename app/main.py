from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

import db
import cache
from handlers import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.connect()
    await cache.connect()
    yield
    await cache.disconnect()
    await db.disconnect()


app = FastAPI(
    title="OTUS Highload Architect",
    version="1.2.0",
    lifespan=lifespan,
)

app.include_router(router)