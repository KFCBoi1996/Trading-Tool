from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.data.mock_provider import DeterministicMockMarketProvider
from app.db.models import Candle, SignalOutcome, StrategySignal, TradePlan
from app.observability import get_logger

log = get_logger("app.outcomes")


def _ensure_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


class OutcomeTracker:
    """Determine TP/SL/expiry outcomes for open signals using stored candles."""

    def __init__(self) -> None:
        self.provider = DeterministicMockMarketProvider()

    def _candles_after(self, db: Session, instrument: str, timeframe: str, after: datetime) -> list[Candle]:
        stmt = (
            select(Candle)
            .where(Candle.instrument == instrument, Candle.timeframe == timeframe, Candle.timestamp > after)
            .order_by(Candle.timestamp.asc())
        )
        return list(db.execute(stmt).scalars().all())

    def track(self, db: Session) -> dict[str, int]:
        unresolved_subq = (
            select(SignalOutcome.signal_id).where(SignalOutcome.outcome != "still_open").subquery()
        )
        open_signals = list(
            db.execute(
                select(StrategySignal)
                .where(~StrategySignal.id.in_(select(unresolved_subq.c.signal_id)))
                .order_by(desc(StrategySignal.created_at))
                .limit(200)
            )
            .scalars()
            .all()
        )
        if not open_signals:
            return {"checked": 0, "updated": 0}
        updated = 0
        for signal in open_signals:
            plan = db.execute(
                select(TradePlan).where(TradePlan.signal_id == signal.id).order_by(desc(TradePlan.created_at)).limit(1)
            ).scalars().first()
            if plan is None or plan.stop_loss is None or plan.tp1 is None or plan.entry_low is None:
                continue
            signal_created_at = _ensure_utc(signal.created_at)
            candles = self._candles_after(db, signal.instrument, signal.timeframe, signal_created_at)
            outcome, ambiguous, ambiguity_reason, closed_at = self._classify(signal, plan, candles)
            if outcome is None:
                continue
            closed_at = _ensure_utc(closed_at)
            risk = abs(plan.entry_high - plan.stop_loss) if signal.direction == "long" else abs(plan.stop_loss - plan.entry_low)
            realized_r = self._realized_r(signal, plan, outcome, risk)
            duration_minutes: int | None = None
            if closed_at is not None and signal_created_at is not None:
                duration_minutes = int((closed_at - signal_created_at).total_seconds() / 60)
            db.add(
                SignalOutcome(
                    signal_id=signal.id,
                    outcome=outcome,
                    realized_r=realized_r,
                    mfe_r=None,
                    mae_r=None,
                    time_to_outcome_minutes=duration_minutes,
                    ambiguous_outcome=ambiguous,
                    ambiguity_reason=ambiguity_reason,
                    closed_at=closed_at,
                )
            )
            updated += 1
        if updated:
            db.commit()
        log.info("outcome_tracking_complete", extra={"checked": len(open_signals), "updated": updated})
        return {"checked": len(open_signals), "updated": updated}

    @staticmethod
    def _classify(signal: StrategySignal, plan: TradePlan, candles: list[Candle]):
        if not candles:
            return "still_open", False, None, None
        for candle in candles:
            if signal.direction == "long":
                hit_sl = candle.low <= plan.stop_loss
                hit_tp1 = candle.high >= plan.tp1
                hit_tp2 = plan.tp2 is not None and candle.high >= plan.tp2
            elif signal.direction == "short":
                hit_sl = candle.high >= plan.stop_loss
                hit_tp1 = candle.low <= plan.tp1
                hit_tp2 = plan.tp2 is not None and candle.low <= plan.tp2
            else:
                return "expired", False, "Non-directional signal", candle.timestamp
            if hit_sl and (hit_tp1 or hit_tp2):
                return "ambiguous", True, "SL and TP both touched within the same candle; intrabar order unknown", candle.timestamp
            if hit_tp2:
                return "tp2_hit_before_sl", False, None, candle.timestamp
            if hit_tp1:
                return "tp1_hit_before_sl", False, None, candle.timestamp
            if hit_sl:
                return "sl_hit", False, None, candle.timestamp
            if plan.entry_valid_until and candle.timestamp > plan.entry_valid_until:
                return "expired", False, None, candle.timestamp
        return None, False, None, None

    @staticmethod
    def _realized_r(signal: StrategySignal, plan: TradePlan, outcome: str, risk: float) -> float | None:
        if not risk:
            return None
        if outcome == "tp1_hit_before_sl":
            return plan.rr_to_tp1
        if outcome == "tp2_hit_before_sl":
            return plan.rr_to_tp2
        if outcome == "sl_hit":
            return -1.0
        return None
