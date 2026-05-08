"""FastAPI application entrypoint for the auth service."""
from __future__ import annotations

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from sqlalchemy import text

from .db import Base
from .db import engine
from .routers import auth as auth_router


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Create tables on startup; nothing to do on shutdown."""
    Base.metadata.create_all(engine)
    yield


app = FastAPI(title="Leaf Auth Service", lifespan=lifespan)
app.include_router(auth_router.router, prefix="/auth", tags=["auth"])


@app.get("/health")
def health() -> dict:
    """Liveness + database probe used by docker-compose and Kubernetes."""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {"status": "ok"}
    except Exception:
        return {"status": "degraded"}
