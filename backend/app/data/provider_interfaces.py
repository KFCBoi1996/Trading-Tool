from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from app.schemas import CandleOut, QuoteOut


class ForexCandleProvider(ABC):
    provider_name: str

    @abstractmethod
    def get_candles(self, instrument: str, timeframe: str, start_time: datetime, end_time: datetime) -> list[CandleOut]:
        raise NotImplementedError

    @abstractmethod
    def get_latest_candles(self, instrument: str, timeframe: str, limit: int) -> list[CandleOut]:
        raise NotImplementedError

    @abstractmethod
    def get_latest_quote(self, instrument: str) -> QuoteOut:
        raise NotImplementedError

class EconomicCalendarProvider(ABC):
    provider_name: str

    @abstractmethod
    def get_events(self, start_time: datetime, end_time: datetime, currencies: list[str]) -> list[dict]:
        raise NotImplementedError

class NewsProvider(ABC):
    provider_name: str

    @abstractmethod
    def get_news(self, query: str, currencies: list[str], start_time: datetime, end_time: datetime) -> list[dict]:
        raise NotImplementedError

class RealProviderStub(ForexCandleProvider, EconomicCalendarProvider, NewsProvider):
    provider_name = "real_provider_stub"

    def get_candles(self, instrument: str, timeframe: str, start_time: datetime, end_time: datetime) -> list[CandleOut]:
        raise RuntimeError("Real forex provider is not configured. Set provider API keys before enabling live data.")

    def get_latest_candles(self, instrument: str, timeframe: str, limit: int) -> list[CandleOut]:
        raise RuntimeError("Real forex provider is not configured. Set provider API keys before enabling live data.")

    def get_latest_quote(self, instrument: str) -> QuoteOut:
        raise RuntimeError("Real forex provider is not configured. Set provider API keys before enabling live data.")

    def get_events(self, start_time: datetime, end_time: datetime, currencies: list[str]) -> list[dict]:
        raise RuntimeError("Real calendar provider is not configured. Set provider API keys before enabling live data.")

    def get_news(self, query: str, currencies: list[str], start_time: datetime, end_time: datetime) -> list[dict]:
        raise RuntimeError("Real news provider is not configured. Set provider API keys before enabling live data.")
