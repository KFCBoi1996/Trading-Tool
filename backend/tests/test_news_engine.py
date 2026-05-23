from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.data.mock_provider import DeterministicMockMarketProvider
from app.data.provider_interfaces import EconomicCalendarProvider, NewsProvider
from app.news.engine import NewsCalendarRiskEngine


class _StubCalendar(EconomicCalendarProvider):
    provider_name = "stub_calendar"

    def __init__(self, events: list[dict]) -> None:
        self.events = events

    def get_events(self, start_time: datetime, end_time: datetime, currencies: list[str]) -> list[dict]:
        return [event for event in self.events if start_time <= datetime.fromisoformat(event["event_time"]) <= end_time]


class _StubNews(NewsProvider):
    provider_name = "stub_news"

    def get_news(self, query: str, currencies: list[str], start_time: datetime, end_time: datetime) -> list[dict]:
        return []


def _event(currency: str, importance: str, name: str, offset_minutes: int, mock: bool = False) -> dict:
    return {
        "provider": "stub",
        "event_time": (datetime.now(UTC) + timedelta(minutes=offset_minutes)).isoformat(),
        "country": currency,
        "currency": currency,
        "event_name": name,
        "importance": importance,
        "actual": None,
        "forecast": None,
        "previous": None,
        "data_status": "MOCK" if mock else "LIVE",
        "is_mock": mock,
    }


def test_high_impact_event_in_window_triggers_blackout() -> None:
    calendar = _StubCalendar([_event("USD", "high", "FOMC Rate Decision", offset_minutes=20)])
    engine = NewsCalendarRiskEngine(calendar, _StubNews())
    result = engine.assess("EUR_USD")
    assert result.news_risk_status == "blackout"
    assert result.blackout_active is True


def test_low_impact_event_does_not_trigger_caution() -> None:
    calendar = _StubCalendar([_event("USD", "low", "Random low-impact event", offset_minutes=20)])
    engine = NewsCalendarRiskEngine(calendar, _StubNews())
    result = engine.assess("EUR_USD")
    assert result.news_risk_status == "clear"
    assert result.blackout_active is False


def test_medium_impact_event_in_caution_window_marks_caution() -> None:
    calendar = _StubCalendar([_event("USD", "medium", "ISM PMI Release", offset_minutes=15)])
    engine = NewsCalendarRiskEngine(calendar, _StubNews())
    result = engine.assess("EUR_USD")
    assert result.news_risk_status in {"caution", "blackout"}


def test_mock_news_engine_marks_data_status_mock() -> None:
    provider = DeterministicMockMarketProvider()
    engine = NewsCalendarRiskEngine(provider, provider)
    result = engine.assess("EUR_USD")
    assert result.data_status == "MOCK"
    assert result.is_mock is True
