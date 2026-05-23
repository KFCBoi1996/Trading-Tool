from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.config import get_settings
from app.db.session import engine
from app.schemas import HealthOut


class HealthService:
    def status(self) -> HealthOut:
        settings = get_settings()
        database_status = "ok"
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
        except SQLAlchemyError:
            database_status = "unavailable"
        checks = {
            "backend": "ok",
            "database": database_status,
            "market_provider": "mock" if settings.mock_data_enabled else ("real" if settings.forex_data_provider != "mock" else "unconfigured"),
            "llm_provider": "configured" if settings.llm_api_key or settings.openai_api_key else "rules_only_stub",
            "trade_execution": "not_present",
        }
        overall = "healthy" if database_status == "ok" else "degraded"
        return HealthOut(
            status=overall,
            service="backend",
            mock_data_enabled=settings.mock_data_enabled,
            live_recommendations_enabled=settings.live_recommendations_enabled,
            feature_flags=settings.feature_flags,
            checks=checks,
        )
