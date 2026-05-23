from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.provider import LLMProvider
from app.arbiter.final_arbiter import FinalArbiter
from app.audit.service import AuditService
from app.config import get_settings
from app.constants import BLOCKING_DATA_STATUSES, SUPPORTED_INSTRUMENTS
from app.data.correlation_context import CorrelationContextEngine
from app.data.mock_provider import DeterministicMockMarketProvider
from app.data.reconciliation import ProviderReconciliationEngine
from app.db.models import (
    Candle,
    EconomicEvent,
    NewsItem,
    Quote,
    RankedSetup,
    RegimeSnapshot,
    StrategySignal,
    TradePlan,
)
from app.features.engine import FeatureEngine
from app.news.engine import NewsCalendarRiskEngine
from app.observability import get_logger
from app.ranking.engine import RankingEngine
from app.regime.engine import RegimeEngine
from app.risk.engine import RiskEngine
from app.schemas import CandleOut, DataQualityStatus, QuoteOut, RecommendationOut
from app.strategies.base import StrategyContext
from app.strategies.plugins import get_strategy_instances

log = get_logger("app.journal")


class SignalJournalService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.provider = DeterministicMockMarketProvider()
        self.feature_engine = FeatureEngine()
        self.regime_engine = RegimeEngine()
        self.news_engine = NewsCalendarRiskEngine(self.provider, self.provider)
        self.risk_engine = RiskEngine()
        self.ranking_engine = RankingEngine()
        self.ai_provider = LLMProvider()
        self.arbiter = FinalArbiter()
        self.audit = AuditService()
        self.reconciliation = ProviderReconciliationEngine()
        self.correlation = CorrelationContextEngine()

    def persist_candles(self, db: Session, candles: Iterable[CandleOut]) -> int:
        candles = list(candles)
        if not candles:
            return 0
        keys = {(c.provider, c.instrument, c.timeframe, c.timestamp) for c in candles}
        existing = set(
            db.execute(
                select(Candle.provider, Candle.instrument, Candle.timeframe, Candle.timestamp).where(
                    Candle.provider.in_({k[0] for k in keys})
                )
            ).all()
        )
        inserted = 0
        for candle in candles:
            key = (candle.provider, candle.instrument, candle.timeframe, candle.timestamp)
            if key in existing:
                continue
            db.add(Candle(**candle.model_dump()))
            inserted += 1
        if inserted:
            db.commit()
        return inserted

    def persist_quote(self, db: Session, quote: QuoteOut) -> None:
        db.add(Quote(**quote.model_dump()))
        db.commit()

    def persist_news_and_events(self, db: Session, instrument: str) -> dict[str, int]:
        meta = SUPPORTED_INSTRUMENTS[instrument]
        now = datetime.now(UTC)
        events = self.provider.get_events(now - timedelta(hours=1), now + timedelta(hours=24), [meta["base"], meta["quote"]])
        for event in events:
            payload = dict(event)
            payload["event_time"] = datetime.fromisoformat(str(payload["event_time"]))
            db.add(EconomicEvent(**payload))
        news = self.provider.get_news(instrument, [meta["base"], meta["quote"]], now - timedelta(hours=12), now)
        for item in news:
            payload = dict(item)
            payload["published_at"] = datetime.fromisoformat(str(payload["published_at"]))
            db.add(NewsItem(**payload))
        db.commit()
        return {"events": len(events), "news": len(news)}

    def _data_quality(self, instrument: str, candles: list[CandleOut], quote: QuoteOut | None) -> DataQualityStatus:
        latest = candles[-1] if candles else None
        passed = bool(
            latest
            and quote
            and latest.complete
            and latest.data_status not in BLOCKING_DATA_STATUSES
            and quote.data_status not in BLOCKING_DATA_STATUSES
        )
        reason = None
        if not latest:
            reason = "Missing latest candle"
        elif not quote:
            reason = "Missing quote/spread"
        elif latest.data_status in BLOCKING_DATA_STATUSES:
            reason = f"Candle data status {latest.data_status} blocks recommendation"
        elif quote.data_status in BLOCKING_DATA_STATUSES:
            reason = f"Quote data status {quote.data_status} blocks recommendation"
        return DataQualityStatus(
            instrument=instrument,
            data_status=latest.data_status if latest else "UNAVAILABLE",
            data_provider=latest.provider if latest else "UNAVAILABLE",
            latest_candle_timestamp=latest.timestamp if latest else None,
            latest_quote_timestamp=quote.timestamp if quote else None,
            data_quality_passed=passed,
            data_quality_rejection_reason=reason,
        )

    def scan_instrument(self, db: Session, instrument: str) -> RecommendationOut:
        if instrument not in SUPPORTED_INSTRUMENTS:
            raise ValueError(f"Unsupported instrument: {instrument}")
        setup_candles = self.provider.get_latest_candles(instrument, "H1", 240)
        trigger_candles = self.provider.get_latest_candles(instrument, "M15", 240)
        h4_candles = self.provider.get_latest_candles(instrument, "H4", 240)
        self.persist_candles(db, setup_candles + trigger_candles + h4_candles)
        quote = self.provider.get_latest_quote(instrument)
        setup_features = self.feature_engine.calculate(instrument, "H1", setup_candles, quote)
        trigger_features = self.feature_engine.calculate(instrument, "M15", trigger_candles, quote)
        regime_features = self.feature_engine.calculate(instrument, "H4", h4_candles, quote)
        regime = self.regime_engine.classify(regime_features)
        news_risk = self.news_engine.assess(instrument)
        data_quality = self._data_quality(instrument, setup_candles, quote)
        context = StrategyContext(
            instrument=instrument,
            setup_timeframe="H1",
            trigger_timeframe="M15",
            setup_features=setup_features,
            trigger_features=trigger_features,
            quote=quote,
            regime=regime,
            news_risk=news_risk,
        )
        signals = [strategy.evaluate(context) for strategy in get_strategy_instances()]

        def score_seed(sig) -> float:
            preference_bonus = 8 if sig.strategy_id in regime.preferred_strategies else 0
            rejection_penalty = 25 if sig.status == "rejected" else 0
            return sig.raw_confidence - rejection_penalty + preference_bonus

        signal = max(signals, key=score_seed)
        signal_row = StrategySignal(
            instrument=signal.instrument,
            timeframe=signal.timeframe,
            trigger_timeframe=signal.trigger_timeframe,
            strategy_id=signal.strategy_id,
            strategy_version=signal.strategy_version,
            strategy_family=signal.strategy_family,
            direction=signal.direction,
            status=signal.status,
            entry_low=signal.entry_zone.get("low"),
            entry_high=signal.entry_zone.get("high"),
            suggested_stop=signal.suggested_stop,
            suggested_tp1=signal.suggested_targets[0] if signal.suggested_targets else None,
            suggested_tp2=signal.suggested_targets[1] if len(signal.suggested_targets) > 1 else None,
            raw_confidence=signal.raw_confidence,
            evidence_json=[e.model_dump() for e in signal.evidence],
            risk_flags_json=[r.model_dump() for r in signal.risk_flags],
            source_candle_timestamp=signal.source_candle_timestamp,
            data_status=signal.data_status,
            is_mock=signal.is_mock,
        )
        db.add(signal_row)
        db.flush()
        signal_with_id = signal.model_copy(update={"id": signal_row.id})
        db.add(
            RegimeSnapshot(
                instrument=regime.instrument,
                timeframe=regime.timeframe,
                trend_state=regime.trend_state,
                trend_strength=regime.trend_strength,
                range_strength=regime.range_strength,
                volatility_state=regime.volatility_state,
                session_state=regime.session_state,
                preferred_strategies_json=regime.preferred_strategies,
                blocked_strategies_json=regime.blocked_strategies,
                data_status=regime.data_status,
                is_mock=regime.is_mock,
            )
        )
        risk_plan = self.risk_engine.build_plan(signal_with_id, setup_features, quote, news_risk)
        ranking = self.ranking_engine.rank(signal_with_id, regime, news_risk, risk_plan, data_quality.data_quality_passed)
        ranked_row = RankedSetup(
            signal_id=signal_row.id,
            ranking_version=ranking.ranking_version,
            final_score=ranking.final_score,
            score_breakdown_json=ranking.score_breakdown,
            decision=ranking.decision,
            rejection_reason=ranking.rejection_reason,
        )
        db.add(ranked_row)
        db.add(
            TradePlan(
                signal_id=signal_row.id,
                risk_engine_version=risk_plan.risk_engine_version,
                instrument=signal_with_id.instrument,
                direction=signal_with_id.direction,
                entry_type=risk_plan.entry_type,
                entry_low=risk_plan.entry_low,
                entry_high=risk_plan.entry_high,
                stop_loss=risk_plan.stop_loss,
                tp1=risk_plan.tp1,
                tp2=risk_plan.tp2,
                rr_to_tp1=risk_plan.rr_to_tp1,
                rr_to_tp2=risk_plan.rr_to_tp2,
                invalidation=risk_plan.invalidation,
                stop_reason=risk_plan.stop_reason,
                tp_reason=risk_plan.tp_reason,
                entry_valid_until=risk_plan.entry_valid_until,
                valid_for_candles=risk_plan.valid_for_candles,
                missed_entry=risk_plan.missed_entry,
            )
        )
        db.commit()
        ai_analysis = self.ai_provider.generate_structured_analysis(signal_with_id, ranking, risk_plan, news_risk.news_risk_status)
        risk_review = self.ai_provider.run_risk_review(signal_with_id, ranking, risk_plan, news_risk.news_risk_status)
        final = self.arbiter.decide(
            data_quality.data_status,
            data_quality.data_quality_passed,
            news_risk,
            ranking,
            risk_plan,
            risk_review,
            self.settings.feature_flags,
        )
        reasons = [
            reason
            for reason in [
                data_quality.data_quality_rejection_reason,
                ranking.rejection_reason,
                risk_plan.rejection_reason,
                risk_review.rejection_reason,
                final.rejection_reason,
            ]
            if reason
        ]
        recommendation = RecommendationOut(
            signal_id=signal_row.id,
            instrument=instrument,
            data_status=data_quality.data_status,
            data_provider=data_quality.data_provider,
            latest_candle_timestamp=data_quality.latest_candle_timestamp,
            latest_quote_timestamp=data_quality.latest_quote_timestamp,
            data_quality_passed=data_quality.data_quality_passed,
            data_quality_rejection_reason=data_quality.data_quality_rejection_reason,
            strategy_signal=signal_with_id,
            regime=regime,
            news_risk=news_risk,
            reconciliation=self.reconciliation.reconcile(instrument, "H1", [self.provider.provider_name], data_quality.data_status),
            correlation_context=self.correlation.get_context(instrument),
            ranking=ranking,
            risk_plan=risk_plan,
            ai_analysis=ai_analysis,
            risk_review=risk_review,
            final_arbiter=final,
            no_trade_explanation={
                "reasons": reasons or ["No hard rejection was produced."],
                "could_become_valid_if": [
                    "Connect LIVE data provider keys",
                    "Disable paper validation only after challenger validation",
                    "Clear all hard risk gates",
                ],
                "expired": False,
                "blocked_by_mock_data": signal_with_id.is_mock,
            },
            is_mock=signal_with_id.is_mock,
        )
        recommendation.audit_id = self.audit.record(db, recommendation)
        log.info(
            "scan_complete",
            extra={
                "instrument": instrument,
                "signal_id": signal_row.id,
                "decision": final.final_decision,
                "score": ranking.final_score,
                "data_status": data_quality.data_status,
            },
        )
        return recommendation

    def scan_all(self, db: Session) -> list[RecommendationOut]:
        return [self.scan_instrument(db, instrument) for instrument in SUPPORTED_INSTRUMENTS]

    def worker_status(self) -> dict:
        return {
            "service": "worker",
            "status": "healthy",
            "last_heartbeat": datetime.now(UTC).isoformat(),
            "mock_data_enabled": self.settings.mock_data_enabled,
        }
