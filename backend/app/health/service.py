from __future__ import annotations

from app.config import get_settings
from app.schemas import HealthOut

class HealthService:
    def status(self) -> HealthOut:
        settings = get_settings()
        checks = {
            "backend": "ok",
            "database": "configured",
            "market_provider": "mock" if settings.mock_data_enabled else "unconfigured",
            "llm_provider": "configured" if settings.llm_api_key or settings.openai_api_key else "rules_only_stub",
            "trade_execution": "not_present",
        }
        return HealthOut(status="healthy", service="backend", mock_data_enabled=settings.mock_data_enabled, live_recommendations_enabled=settings.live_recommendations_enabled, feature_flags=settings.feature_flags, checks=checks)
