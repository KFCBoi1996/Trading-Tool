from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from .constants import FEATURE_FLAGS


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "FX Signal Intelligence MVP"
    environment: str = Field(default="local", alias="ENVIRONMENT")
    database_url: str = Field(default="sqlite+pysqlite:///./fx_signal_intelligence.db", alias="DATABASE_URL")
    redis_url: str | None = Field(default=None, alias="REDIS_URL")
    forex_data_provider: str = Field(default="mock", alias="FOREX_DATA_PROVIDER")
    forex_api_key: str | None = Field(default=None, alias="FOREX_API_KEY")
    calendar_data_provider: str = Field(default="mock", alias="CALENDAR_DATA_PROVIDER")
    calendar_api_key: str | None = Field(default=None, alias="CALENDAR_API_KEY")
    news_data_provider: str = Field(default="mock", alias="NEWS_DATA_PROVIDER")
    news_api_key: str | None = Field(default=None, alias="NEWS_API_KEY")
    llm_api_key: str | None = Field(default=None, alias="LLM_API_KEY")
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    mock_data_enabled: bool = Field(default=True, alias="MOCK_DATA_ENABLED")
    live_recommendations_enabled: bool = Field(default=False, alias="LIVE_RECOMMENDATIONS_ENABLED")
    paper_validation_mode_enabled: bool = Field(default=True, alias="PAPER_VALIDATION_MODE_ENABLED")
    allow_delayed_recommendations: bool = Field(default=False, alias="ALLOW_DELAYED_RECOMMENDATIONS")
    cors_origins: str = Field(default="http://localhost:3000", alias="CORS_ORIGINS")

    @property
    def feature_flags(self) -> dict[str, bool]:
        flags = dict(FEATURE_FLAGS)
        flags["MOCK_DATA_ENABLED"] = self.mock_data_enabled
        flags["LIVE_RECOMMENDATIONS_ENABLED"] = self.live_recommendations_enabled
        flags["PAPER_VALIDATION_MODE_ENABLED"] = self.paper_validation_mode_enabled
        flags["LIVE_PROVIDER_ENABLED"] = self.forex_data_provider != "mock" and bool(self.forex_api_key)
        flags["AI_ANALYST_ENABLED"] = bool(self.llm_api_key or self.openai_api_key)
        flags["AI_RISK_REVIEWER_ENABLED"] = bool(self.llm_api_key or self.openai_api_key)
        return flags

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

@lru_cache
def get_settings() -> Settings:
    return Settings()
