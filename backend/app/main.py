from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.routes import router
from app.config import get_settings
from app.db.init_db import create_db_and_tables, seed_reference_data
from app.db.session import SessionLocal, engine
from app.observability import configure_logging, get_logger
from app.observability.errors import install_error_handlers
from app.observability.middleware import RequestContextMiddleware

settings = get_settings()
log = get_logger("app.startup")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    configure_logging()
    create_db_and_tables()
    db = SessionLocal()
    try:
        seed_reference_data(db)
    finally:
        db.close()
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        log.info("startup_complete", extra={"environment": settings.environment, "live_recommendations": settings.live_recommendations_enabled})
    except Exception:
        log.exception("database_unavailable_on_startup")
    yield
    log.info("shutdown_complete")


app = FastAPI(
    title="FX Signal Intelligence MVP",
    description="Decision-support forex signal intelligence. No trade execution endpoints exist.",
    version="0.1.0",
    lifespan=lifespan,
)
app.add_middleware(RequestContextMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
install_error_handlers(app)
app.include_router(router)


@app.get("/")
def root() -> dict:
    return {"service": settings.app_name, "message": "Decision-support only. No trade execution."}
