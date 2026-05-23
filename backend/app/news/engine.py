from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.constants import SUPPORTED_INSTRUMENTS
from app.data.provider_interfaces import EconomicCalendarProvider, NewsProvider
from app.schemas import Evidence, NewsRiskOut

HIGH_IMPACT_KEYWORDS = ("rate", "central bank", "cpi", "inflation", "jobs", "nfp", "gdp", "retail", "pmi", "ppi", "fomc", "ecb", "boe", "boj")

class NewsCalendarRiskEngine:
    def __init__(self, calendar_provider: EconomicCalendarProvider, news_provider: NewsProvider):
        self.calendar_provider = calendar_provider
        self.news_provider = news_provider

    def assess(self, instrument: str) -> NewsRiskOut:
        meta = SUPPORTED_INSTRUMENTS[instrument]
        currencies = [meta["base"], meta["quote"]]
        now = datetime.now(UTC)
        events = self.calendar_provider.get_events(now - timedelta(hours=1), now + timedelta(hours=24), currencies)
        next_event = min(events, key=lambda event: event["event_time"], default=None)
        blackout_active = False
        status = "clear"
        if next_event:
            event_time = datetime.fromisoformat(next_event["event_time"])
            minutes_to_event = (event_time - now).total_seconds() / 60
            importance = str(next_event.get("importance", "low")).lower()
            event_name = str(next_event.get("event_name", "")).lower()
            is_high_impact = importance == "high" or any(keyword in event_name for keyword in HIGH_IMPACT_KEYWORDS)
            if is_high_impact and -20 <= minutes_to_event <= 45:
                blackout_active = True
                status = "blackout"
            elif importance in {"medium", "high"} and -10 <= minutes_to_event <= 20:
                status = "caution"
        headlines = self.news_provider.get_news(instrument, currencies, now - timedelta(hours=12), now)
        data_status = "MOCK" if any(item.get("is_mock") for item in headlines + events) else "LIVE"
        return NewsRiskOut(
            instrument=instrument,
            news_risk_status=status,  # type: ignore[arg-type]
            blackout_active=blackout_active,
            next_event=next_event,
            headline_sentiment={"directional_bias": "neutral", "confidence": 0.0, "summary": "Live headline sentiment unavailable; mock/scaffold summary only."},
            evidence=[Evidence(evidence_id=f"news:{instrument}:risk", text=f"Calendar/news risk status is {status}.", source="news_engine")],
            data_status=data_status,  # type: ignore[arg-type]
            is_mock=data_status == "MOCK",
        )
