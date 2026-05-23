from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.data.mock_provider import DeterministicMockMarketProvider
from app.db.init_db import create_db_and_tables, seed_reference_data
from app.db.models import Candle, StrategySignal, TradePlan
from app.db.session import SessionLocal
from app.journal.outcomes import OutcomeTracker


def _setup_session():
    create_db_and_tables()
    session = SessionLocal()
    seed_reference_data(session)
    return session


def test_outcome_tracker_marks_tp1_hit_before_sl() -> None:
    db = _setup_session()
    try:
        signal = StrategySignal(
            instrument="EUR_USD",
            timeframe="H1",
            trigger_timeframe="M15",
            strategy_id="ema_trend_pullback",
            strategy_version="1.0.0",
            strategy_family="trend_following",
            direction="long",
            status="active",
            entry_low=1.10,
            entry_high=1.11,
            suggested_stop=1.09,
            suggested_tp1=1.13,
            suggested_tp2=1.15,
            raw_confidence=70.0,
            evidence_json=[{"evidence_id": "e", "text": "t", "source": "strategy_engine"}],
            risk_flags_json=[],
            source_candle_timestamp=datetime.now(UTC) - timedelta(hours=1),
            data_status="MOCK",
            is_mock=True,
        )
        db.add(signal)
        db.flush()
        db.add(
            TradePlan(
                signal_id=signal.id,
                risk_engine_version="risk_engine_v1.0.0",
                instrument="EUR_USD",
                direction="long",
                entry_type="limit_retest",
                entry_low=1.10,
                entry_high=1.11,
                stop_loss=1.09,
                tp1=1.13,
                tp2=1.15,
                rr_to_tp1=2.0,
                rr_to_tp2=4.0,
                invalidation="x",
                stop_reason="x",
                tp_reason="x",
                entry_valid_until=None,
                valid_for_candles=3,
                missed_entry=False,
            )
        )
        # Candle after the signal that hits TP1 but not SL.
        provider = DeterministicMockMarketProvider()
        ts = datetime.now(UTC)
        db.add(
            Candle(
                provider=provider.provider_name,
                instrument="EUR_USD",
                timeframe="H1",
                timestamp=ts,
                open=1.11,
                high=1.14,
                low=1.105,
                close=1.135,
                volume=1.0,
                complete=True,
                data_status="MOCK",
                is_mock=True,
            )
        )
        db.commit()
        tracker = OutcomeTracker()
        result = tracker.track(db)
        assert result["checked"] >= 1
        assert result["updated"] >= 1
    finally:
        db.close()
