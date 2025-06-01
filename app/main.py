from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

import db
from handlers import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.connect()
    yield
    await db.disconnect()


app = FastAPI(
    title="OTUS Highload Architect",
    version="1.2.0",
    lifespan=lifespan,
)

app.include_router(router)