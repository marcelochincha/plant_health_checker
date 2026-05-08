"""FastAPI application entrypoint for the classifier service."""
from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from .config import settings
from .db import Base
from .db import engine
from .inference_singleton import get_classifier
from .inference_singleton import init_classifier
from .routers import predict as predict_router


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Create tables and load the model once on startup."""
    Base.metadata.create_all(engine)
    try:
        init_classifier(settings.artifacts_dir)
    except FileNotFoundError:
        # Health endpoint will surface this as model_loaded=False so
        # the service still answers / lets ops debug instead of crash-looping.
        pass
    yield


app = FastAPI(title="Leaf Classifier Service", lifespan=lifespan)
app.include_router(predict_router.router, prefix="/classifier", tags=["classifier"])


@app.get("/health")
def health() -> dict:
    """Liveness + database + model load probe used by orchestration."""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        loaded = get_classifier(allow_none=True) is not None
        return {"status": "ok", "model_loaded": loaded}
    except Exception:
        return {"status": "degraded", "model_loaded": False}
