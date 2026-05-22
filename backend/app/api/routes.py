from __future__ import annotations

from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc
from sqlalchemy.orm import Session
from app.backtesting.engine import BacktestingEngine
from app.config import get_settings
from app.constants import SUPPORTED_INSTRUMENTS, SUPPORTED_TIMEFRAMES
from app.data.mock_provider import DeterministicMockMarketProvider
from app.db.models import FeatureFlag, RecommendationAuditLog, SignalOutcome, StrategySignal
from app.db.session import get_db
from app.health.service import HealthService
from app.journal.service import SignalJournalService
from app.schemas import HealthOut, RecommendationOut

router = APIRouter(prefix="/api")
provider = DeterministicMockMarketProvider()
journal_service = SignalJournalService()
health_service = HealthService()
backtesting_engine = BacktestingEngine()

@router.get("/health", response_model=HealthOut)
def health() -> HealthOut:
    return health_service.status()

@router.get("/admin/health")
def admin_health(db: Session = Depends(get_db)) -> dict:
    status = health_service.status().model_dump()
    status["worker"] = journal_service.worker_status()
    status["recommendation_counts_by_decision_type"] = {
        row.final_decision: db.query(RecommendationAuditLog).filter(RecommendationAuditLog.final_decision == row.final_decision).count()
        for row in db.query(RecommendationAuditLog).all()
    }
    status["open_signals_count"] = db.query(StrategySignal).count()
    status["mock_data_status"] = "MOCK_DATA enabled" if get_settings().mock_data_enabled else "mock disabled"
    return status

@router.get("/instruments")
def instruments() -> list[dict]:
    return [{"symbol": symbol, **meta, "is_active": True} for symbol, meta in SUPPORTED_INSTRUMENTS.items()]

@router.get("/candles/{instrument}")
def candles(instrument: str, timeframe: str = "M15", limit: int = 200) -> list[dict]:
    _validate_instrument_timeframe(instrument, timeframe)
    return [c.model_dump(mode="json") for c in provider.get_latest_candles(instrument, timeframe, min(max(limit, 1), 500))]

@router.get("/quotes/{instrument}")
def quote(instrument: str) -> dict:
    _validate_instrument_timeframe(instrument, "M15")
    return provider.get_latest_quote(instrument).model_dump(mode="json")

@router.get("/spread/{instrument}")
def spread(instrument: str) -> dict:
    q = quote(instrument)
    return {"instrument": instrument, "spread": q["spread"], "spread_pips": q["spread_pips"], "data_status": q["data_status"], "is_mock": q["is_mock"]}

@router.get("/data-status/{instrument}")
def data_status(instrument: str) -> dict:
    _validate_instrument_timeframe(instrument, "M15")
    latest = provider.get_latest_candles(instrument, "M15", 1)[-1]
    q = provider.get_latest_quote(instrument)
    return {
        "instrument": instrument,
        "data_status": "MOCK",
        "data_provider": provider.provider_name,
        "latest_candle_timestamp": latest.timestamp.isoformat(),
        "latest_quote_timestamp": q.timestamp.isoformat(),
        "data_quality_passed": False,
        "data_quality_rejection_reason": "MOCK data blocks live recommendations",
    }

@router.post("/scan", response_model=list[RecommendationOut])
def scan(db: Session = Depends(get_db)) -> list[RecommendationOut]:
    return journal_service.scan_all(db)

@router.get("/signals")
def signals(db: Session = Depends(get_db)) -> list[dict]:
    rows = db.query(StrategySignal).order_by(desc(StrategySignal.created_at)).limit(100).all()
    return [_signal_to_dict(row) for row in rows]

@router.get("/signals/top")
def top_signals(db: Session = Depends(get_db)) -> list[dict]:
    rows = db.query(StrategySignal).order_by(desc(StrategySignal.raw_confidence)).limit(20).all()
    return [_signal_to_dict(row) for row in rows]

@router.get("/signals/rejected")
def rejected_signals(db: Session = Depends(get_db)) -> list[dict]:
    rows = db.query(StrategySignal).filter(StrategySignal.status == "rejected").order_by(desc(StrategySignal.created_at)).limit(100).all()
    return [_signal_to_dict(row) for row in rows]

@router.get("/signals/{signal_id}")
def signal_detail(signal_id: str, db: Session = Depends(get_db)) -> dict:
    row = db.get(StrategySignal, signal_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Signal not found")
    return _signal_to_dict(row)

@router.get("/recommendations/signal/{signal_id}")
def recommendation_by_signal(signal_id: str, db: Session = Depends(get_db)) -> dict:
    audit = db.query(RecommendationAuditLog).filter(RecommendationAuditLog.signal_id == signal_id).order_by(desc(RecommendationAuditLog.created_at)).first()
    if audit is None:
        raise HTTPException(status_code=404, detail="Recommendation audit not found")
    return _audit_to_dict(audit)

@router.get("/recommendations/{instrument}", response_model=RecommendationOut)
def recommendation(instrument: str, db: Session = Depends(get_db)) -> RecommendationOut:
    _validate_instrument_timeframe(instrument, "M15")
    return journal_service.scan_instrument(db, instrument)

@router.get("/trade-plans/{signal_id}")
def trade_plan(signal_id: str, db: Session = Depends(get_db)) -> dict:
    audit = db.query(RecommendationAuditLog).filter(RecommendationAuditLog.signal_id == signal_id).order_by(desc(RecommendationAuditLog.created_at)).first()
    if audit is None:
        raise HTTPException(status_code=404, detail="Trade plan not found")
    return audit.risk_plan_json

@router.get("/calendar/{instrument}")
def calendar(instrument: str) -> list[dict]:
    _validate_instrument_timeframe(instrument, "M15")
    meta = SUPPORTED_INSTRUMENTS[instrument]
    now = datetime.now(timezone.utc)
    return provider.get_events(now - timedelta(hours=1), now + timedelta(hours=24), [meta["base"], meta["quote"]])

@router.get("/news/{instrument}")
def news(instrument: str) -> list[dict]:
    _validate_instrument_timeframe(instrument, "M15")
    meta = SUPPORTED_INSTRUMENTS[instrument]
    now = datetime.now(timezone.utc)
    return provider.get_news(instrument, [meta["base"], meta["quote"]], now - timedelta(hours=12), now)

@router.get("/news-risk/{instrument}")
def news_risk(instrument: str) -> dict:
    _validate_instrument_timeframe(instrument, "M15")
    return journal_service.news_engine.assess(instrument).model_dump(mode="json")

@router.post("/backtest/run")
def run_backtest(strategy_id: str = "ema_trend_pullback", instrument: str = "EUR_USD", timeframe: str = "H1") -> dict:
    _validate_instrument_timeframe(instrument, timeframe)
    return backtesting_engine.summarize(strategy_id, "1.0.0", instrument, timeframe).model_dump()

@router.get("/backtest/results")
def backtest_results() -> list[dict]:
    return [backtesting_engine.summarize("ema_trend_pullback", "1.0.0", instrument, "H1").model_dump() for instrument in SUPPORTED_INSTRUMENTS]

@router.get("/backtest/summary/{strategy_id}")
def backtest_summary(strategy_id: str, instrument: str = "EUR_USD", timeframe: str = "H1") -> dict:
    return backtesting_engine.summarize(strategy_id, "1.0.0", instrument, timeframe).model_dump()

@router.get("/journal")
def journal(db: Session = Depends(get_db)) -> list[dict]:
    audits = db.query(RecommendationAuditLog).order_by(desc(RecommendationAuditLog.created_at)).limit(100).all()
    return [_audit_to_dict(audit) for audit in audits]

@router.get("/journal/stats")
def journal_stats(db: Session = Depends(get_db)) -> dict:
    total = db.query(RecommendationAuditLog).count()
    no_trade = db.query(RecommendationAuditLog).filter(RecommendationAuditLog.final_decision.like("REJECTED%")) .count()
    outcomes = db.query(SignalOutcome).count()
    return {"total_decisions": total, "rejected_or_no_trade": no_trade, "outcomes_tracked": outcomes, "mock_data_rows": db.query(StrategySignal).filter(StrategySignal.is_mock.is_(True)).count()}

@router.post("/journal/outcome/update")
def update_outcome(signal_id: str, outcome: str, db: Session = Depends(get_db)) -> dict:
    row = SignalOutcome(signal_id=signal_id, outcome=outcome, ambiguous_outcome=outcome == "ambiguous", ambiguity_reason="Manual/API update marked ambiguous" if outcome == "ambiguous" else None)
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"id": row.id, "signal_id": row.signal_id, "outcome": row.outcome, "ambiguous_outcome": row.ambiguous_outcome}

@router.get("/audit/{signal_id}")
def audit(signal_id: str, db: Session = Depends(get_db)) -> list[dict]:
    rows = db.query(RecommendationAuditLog).filter(RecommendationAuditLog.signal_id == signal_id).order_by(desc(RecommendationAuditLog.created_at)).all()
    return [_audit_to_dict(row) for row in rows]

@router.post("/alerts")
def create_alert(signal_id: str, alert_type: str = "watchlist_setup") -> dict:
    return {"status": "not_created", "reason": "Alerts require arbiter approval; direct alert creation is scaffolded for MVP."}

@router.get("/alerts")
def alerts() -> list[dict]:
    return []

@router.delete("/alerts/{alert_id}")
def delete_alert(alert_id: str) -> dict:
    return {"alert_id": alert_id, "status": "deleted_if_present"}

@router.get("/feature-flags")
def feature_flags(db: Session = Depends(get_db)) -> list[dict]:
    rows = db.query(FeatureFlag).all()
    if not rows:
        return [{"flag_name": name, "enabled": enabled} for name, enabled in get_settings().feature_flags.items()]
    return [{"flag_name": row.flag_name, "enabled": row.enabled, "description": row.description} for row in rows]

@router.patch("/feature-flags/{flag_name}")
def patch_feature_flag(flag_name: str, enabled: bool, db: Session = Depends(get_db)) -> dict:
    row = db.query(FeatureFlag).filter(FeatureFlag.flag_name == flag_name).first()
    if row is None:
        raise HTTPException(status_code=404, detail="Feature flag not found")
    row.enabled = enabled
    db.commit()
    return {"flag_name": row.flag_name, "enabled": row.enabled}

def _validate_instrument_timeframe(instrument: str, timeframe: str) -> None:
    if instrument not in SUPPORTED_INSTRUMENTS:
        raise HTTPException(status_code=404, detail="Unsupported instrument")
    if timeframe not in SUPPORTED_TIMEFRAMES:
        raise HTTPException(status_code=400, detail="Unsupported timeframe")

def _signal_to_dict(row: StrategySignal) -> dict:
    return {
        "id": row.id,
        "created_at": row.created_at.isoformat(),
        "instrument": row.instrument,
        "timeframe": row.timeframe,
        "trigger_timeframe": row.trigger_timeframe,
        "strategy_id": row.strategy_id,
        "strategy_version": row.strategy_version,
        "strategy_family": row.strategy_family,
        "direction": row.direction,
        "status": row.status,
        "entry_low": row.entry_low,
        "entry_high": row.entry_high,
        "suggested_stop": row.suggested_stop,
        "suggested_tp1": row.suggested_tp1,
        "suggested_tp2": row.suggested_tp2,
        "raw_confidence": row.raw_confidence,
        "evidence": row.evidence_json,
        "risk_flags": row.risk_flags_json,
        "data_status": row.data_status,
        "is_mock": row.is_mock,
    }

def _audit_to_dict(row: RecommendationAuditLog) -> dict:
    return {
        "id": row.id,
        "created_at": row.created_at.isoformat(),
        "signal_id": row.signal_id,
        "instrument": row.instrument,
        "final_decision": row.final_decision,
        "rejection_reason": row.rejection_reason,
        "data_status": row.data_status,
        "data_provider": row.data_provider,
        "strategy_id": row.strategy_id,
        "strategy_version": row.strategy_version,
        "ranking_version": row.ranking_version,
        "risk_engine_version": row.risk_engine_version,
        "arbiter_version": row.arbiter_version,
        "score_breakdown": row.score_breakdown_json,
        "risk_plan": row.risk_plan_json,
        "news_risk": row.news_risk_json,
        "regime_snapshot": row.regime_snapshot_json,
        "ai_review": row.ai_review_json,
        "risk_review": row.risk_review_json,
    }
