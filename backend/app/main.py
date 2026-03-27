from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import configure_logging
from app.db.init_db import ensure_database_exists
from app.db.session import AsyncSessionLocal
from app.routes.api_v1 import api_router
from app.routes.ws import router as ws_router
from app.services.seed import seed_if_empty

logger = logging.getLogger(__name__)

app = FastAPI(title=settings.app_name, version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
app.include_router(ws_router)


@app.on_event("startup")
async def on_startup() -> None:
    configure_logging(settings.log_level)
    await ensure_database_exists()
    async with AsyncSessionLocal() as db:
        await seed_if_empty(db)
    logger.info("Startup complete.")


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "app": settings.app_name}

