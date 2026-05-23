from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta

from app.constants import SUPPORTED_INSTRUMENTS
from app.schemas import CandleOut, QuoteOut

from .provider_interfaces import EconomicCalendarProvider, ForexCandleProvider, NewsProvider

_TIMEFRAME_MINUTES = {"M15": 15, "H1": 60, "H4": 240}
_BASE_PRICES = {"EUR_USD": 1.0825, "GBP_USD": 1.2710, "USD_JPY": 156.20, "AUD_USD": 0.6650, "USD_CAD": 1.3620}

class DeterministicMockMarketProvider(ForexCandleProvider, EconomicCalendarProvider, NewsProvider):
    provider_name = "MOCK_DATA"

    def _anchor(self, timeframe: str) -> datetime:
        minutes = _TIMEFRAME_MINUTES[timeframe]
        now = datetime.now(UTC).replace(second=0, microsecond=0)
        if timeframe == "M15":
            return now.replace(minute=(now.minute // minutes) * minutes)
        if timeframe == "H1":
            return now.replace(minute=0)
        if timeframe == "H4":
            return now.replace(hour=(now.hour // 4) * 4, minute=0)
        raise ValueError(f"Unsupported timeframe: {timeframe}")

    def _price_at(self, instrument: str, index: int) -> float:
        base = _BASE_PRICES[instrument]
        pip = SUPPORTED_INSTRUMENTS[instrument]["pip_size"]
        precision = SUPPORTED_INSTRUMENTS[instrument]["precision"]
        drift = index * pip * 0.18
        wave = math.sin(index / 5.0) * pip * 8 + math.cos(index / 17.0) * pip * 13
        return round(base + drift + wave, precision)

    def get_candles(self, instrument: str, timeframe: str, start_time: datetime, end_time: datetime) -> list[CandleOut]:
        candles = self.get_latest_candles(instrument, timeframe, 500)
        return [c for c in candles if start_time <= c.timestamp <= end_time]

    def get_latest_candles(self, instrument: str, timeframe: str, limit: int) -> list[CandleOut]:
        if instrument not in SUPPORTED_INSTRUMENTS or timeframe not in _TIMEFRAME_MINUTES:
            raise ValueError("Unsupported instrument or timeframe")
        minutes = _TIMEFRAME_MINUTES[timeframe]
        anchor = self._anchor(timeframe)
        precision = SUPPORTED_INSTRUMENTS[instrument]["precision"]
        pip = SUPPORTED_INSTRUMENTS[instrument]["pip_size"]
        candles: list[CandleOut] = []
        for offset in range(limit, 0, -1):
            idx = limit - offset
            ts = anchor - timedelta(minutes=minutes * offset)
            open_price = self._price_at(instrument, idx)
            close_price = self._price_at(instrument, idx + 1)
            spread = abs(close_price - open_price)
            high = round(max(open_price, close_price) + max(spread, pip * (4 + (idx % 5))), precision)
            low = round(min(open_price, close_price) - max(spread / 2, pip * (3 + (idx % 3))), precision)
            candles.append(CandleOut(
                provider=self.provider_name,
                instrument=instrument,
                timeframe=timeframe,
                timestamp=ts,
                open=open_price,
                high=high,
                low=low,
                close=close_price,
                volume=1000 + idx * 7,
                complete=True,
                data_status="MOCK",
                is_mock=True,
            ))
        return candles

    def get_latest_quote(self, instrument: str) -> QuoteOut:
        latest = self.get_latest_candles(instrument, "M15", 1)[-1]
        pip = SUPPORTED_INSTRUMENTS[instrument]["pip_size"]
        precision = SUPPORTED_INSTRUMENTS[instrument]["precision"]
        spread_pips = 1.2 + (sum(ord(c) for c in instrument) % 7) / 10
        spread = spread_pips * pip
        mid = latest.close
        bid = round(mid - spread / 2, precision)
        ask = round(mid + spread / 2, precision)
        return QuoteOut(
            provider=self.provider_name,
            instrument=instrument,
            timestamp=datetime.now(UTC).replace(second=0, microsecond=0),
            bid=bid,
            ask=ask,
            mid=mid,
            spread=round(ask - bid, precision),
            spread_pips=round(spread_pips, 2),
            data_status="MOCK",
            is_mock=True,
        )

    def get_events(self, start_time: datetime, end_time: datetime, currencies: list[str]) -> list[dict]:
        events: list[dict] = []
        for idx, currency in enumerate(sorted(set(currencies))):
            event_time = (datetime.now(UTC) + timedelta(hours=4 + idx)).replace(minute=30, second=0, microsecond=0)
            if start_time <= event_time <= end_time:
                events.append({
                    "provider": self.provider_name,
                    "event_time": event_time.isoformat(),
                    "country": currency,
                    "currency": currency,
                    "event_name": f"Mock {currency} PMI risk window",
                    "importance": "medium",
                    "actual": None,
                    "forecast": None,
                    "previous": None,
                    "data_status": "MOCK",
                    "is_mock": True,
                })
        return events

    def get_news(self, query: str, currencies: list[str], start_time: datetime, end_time: datetime) -> list[dict]:
        return [{
            "provider": self.provider_name,
            "published_at": datetime.now(UTC).isoformat(),
            "source": "MOCK_DATA",
            "title": f"Mock macro headline for {'/'.join(currencies)}",
            "summary": "Deterministic mock news used because no live news provider key is configured.",
            "url": None,
            "affected_currencies": currencies,
            "sentiment_score": 0.0,
            "relevance_score": 0.25,
            "data_status": "MOCK",
            "is_mock": True,
        }]
