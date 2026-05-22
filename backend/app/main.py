from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.config import get_settings
from app.db.init_db import create_db_and_tables, seed_reference_data
from app.db.session import SessionLocal

settings = get_settings()

app = FastAPI(
    title="FX Signal Intelligence MVP",
    description="Decision-support forex signal intelligence. No trade execution endpoints exist.",
    version="0.1.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)

@app.on_event("startup")
def startup() -> None:
    create_db_and_tables()
    db = SessionLocal()
    try:
        seed_reference_data(db)
    finally:
        db.close()

@app.get("/")
def root() -> dict:
    return {"service": settings.app_name, "message": "Decision-support only. No trade execution."}
