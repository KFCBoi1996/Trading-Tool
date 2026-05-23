from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Annotated, Literal

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.backtesting.engine import BacktestingEngine
from app.config import get_settings
from app.constants import SUPPORTED_INSTRUMENTS, SUPPORTED_TIMEFRAMES
from app.data.mock_provider import DeterministicMockMarketProvider
from app.db.models import (
    Alert,
    FeatureFlag,
    RecommendationAuditLog,
    SignalOutcome,
    StrategySignal,
)
from app.db.session import get_db
from app.health.service import HealthService
from app.journal.outcomes import OutcomeTracker
from app.journal.service import SignalJournalService
from app.observability import get_logger
from app.schemas import HealthOut, RecommendationOut

router = APIRouter(prefix="/api")
provider = DeterministicMockMarketProvider()
journal_service = SignalJournalService()
health_service = HealthService()
backtesting_engine = BacktestingEngine()
outcome_tracker = OutcomeTracker()
log = get_logger("app.api")

InstrumentParam = Annotated[str, Query(min_length=6, max_length=8)]
TimeframeParam = Annotated[str, Query(min_length=2, max_length=3)]


def _validate_instrument(instrument: str) -> None:
    if instrument not in SUPPORTED_INSTRUMENTS:
        raise HTTPException(status_code=404, detail="Unsupported instrument")


def _validate_timeframe(timeframe: str) -> None:
    if timeframe not in SUPPORTED_TIMEFRAMES:
        raise HTTPException(status_code=400, detail="Unsupported timeframe")


@router.get("/health", response_model=HealthOut, tags=["health"])
def health() -> HealthOut:
    return health_service.status()


@router.get("/admin/health", tags=["health"])
def admin_health(db: Session = Depends(get_db)) -> dict:
    status = health_service.status().model_dump()
    status["worker"] = journal_service.worker_status()
    counts = dict(
        db.execute(
            select(RecommendationAuditLog.final_decision, func.count(RecommendationAuditLog.id))
            .group_by(RecommendationAuditLog.final_decision)
        ).all()
    )
    status["recommendation_counts_by_decision_type"] = counts
    status["open_signals_count"] = db.execute(select(func.count(StrategySignal.id))).scalar() or 0
    status["mock_data_status"] = "MOCK_DATA enabled" if get_settings().mock_data_enabled else "mock disabled"
    return status


@router.get("/instruments", tags=["market"])
def instruments() -> list[dict]:
    return [{"symbol": symbol, **meta, "is_active": True} for symbol, meta in SUPPORTED_INSTRUMENTS.items()]


@router.get("/candles/{instrument}", tags=["market"])
def candles(instrument: str, timeframe: str = "M15", limit: int = Query(default=200, ge=1, le=500)) -> list[dict]:
    _validate_instrument(instrument)
    _validate_timeframe(timeframe)
    return [c.model_dump(mode="json") for c in provider.get_latest_candles(instrument, timeframe, limit)]


@router.get("/quotes/{instrument}", tags=["market"])
def quote(instrument: str) -> dict:
    _validate_instrument(instrument)
    return provider.get_latest_quote(instrument).model_dump(mode="json")


@router.get("/spread/{instrument}", tags=["market"])
def spread(instrument: str) -> dict:
    _validate_instrument(instrument)
    q = provider.get_latest_quote(instrument)
    return {
        "instrument": instrument,
        "spread": q.spread,
        "spread_pips": q.spread_pips,
        "data_status": q.data_status,
        "is_mock": q.is_mock,
    }


@router.get("/data-status/{instrument}", tags=["market"])
def data_status(instrument: str) -> dict:
    _validate_instrument(instrument)
    latest = provider.get_latest_candles(instrument, "M15", 1)[-1]
    q = provider.get_latest_quote(instrument)
    return {
        "instrument": instrument,
        "data_status": latest.data_status,
        "data_provider": latest.provider,
        "latest_candle_timestamp": latest.timestamp.isoformat(),
        "latest_quote_timestamp": q.timestamp.isoformat(),
        "data_quality_passed": latest.data_status == "LIVE" and q.data_status == "LIVE",
        "data_quality_rejection_reason": None if latest.data_status == "LIVE" and q.data_status == "LIVE" else f"{latest.data_status} data blocks live recommendations",
    }


@router.post("/scan", response_model=list[RecommendationOut], tags=["signals"])
def scan(db: Session = Depends(get_db)) -> list[RecommendationOut]:
    return journal_service.scan_all(db)


@router.post("/scan/{instrument}", response_model=RecommendationOut, tags=["signals"])
def scan_instrument(instrument: str, db: Session = Depends(get_db)) -> RecommendationOut:
    _validate_instrument(instrument)
    return journal_service.scan_instrument(db, instrument)


@router.get("/signals", tags=["signals"])
def signals(
    db: Session = Depends(get_db),
    status: str | None = Query(default=None, description="Filter by status: active|watchlist|rejected"),
    instrument: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> list[dict]:
    stmt = select(StrategySignal).order_by(desc(StrategySignal.created_at))
    if status:
        stmt = stmt.where(StrategySignal.status == status)
    if instrument:
        _validate_instrument(instrument)
        stmt = stmt.where(StrategySignal.instrument == instrument)
    rows = db.execute(stmt.limit(limit).offset(offset)).scalars().all()
    return [_signal_to_dict(row) for row in rows]


@router.get("/signals/top", tags=["signals"])
def top_signals(db: Session = Depends(get_db), limit: int = Query(default=20, ge=1, le=100)) -> list[dict]:
    rows = db.execute(select(StrategySignal).order_by(desc(StrategySignal.raw_confidence)).limit(limit)).scalars().all()
    return [_signal_to_dict(row) for row in rows]


@router.get("/signals/rejected", tags=["signals"])
def rejected_signals(db: Session = Depends(get_db), limit: int = Query(default=100, ge=1, le=500)) -> list[dict]:
    rows = (
        db.execute(
            select(StrategySignal).where(StrategySignal.status == "rejected").order_by(desc(StrategySignal.created_at)).limit(limit)
        )
        .scalars()
        .all()
    )
    return [_signal_to_dict(row) for row in rows]


@router.get("/signals/{signal_id}", tags=["signals"])
def signal_detail(signal_id: str, db: Session = Depends(get_db)) -> dict:
    row = db.get(StrategySignal, signal_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Signal not found")
    return _signal_to_dict(row)


@router.get("/recommendations/{instrument}", response_model=RecommendationOut, tags=["recommendations"])
def recommendation(instrument: str, db: Session = Depends(get_db)) -> RecommendationOut:
    """Return the latest recommendation for an instrument, scanning if none has been computed."""
    _validate_instrument(instrument)
    latest_audit = db.execute(
        select(RecommendationAuditLog)
        .where(RecommendationAuditLog.instrument == instrument)
        .order_by(desc(RecommendationAuditLog.created_at))
        .limit(1)
    ).scalars().first()
    if latest_audit is None:
        return journal_service.scan_instrument(db, instrument)
    created_at = latest_audit.created_at
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=UTC)
    if created_at < datetime.now(UTC) - timedelta(minutes=15):
        return journal_service.scan_instrument(db, instrument)
    return _audit_to_recommendation(latest_audit)


@router.get("/recommendations/signal/{signal_id}", tags=["recommendations"])
def recommendation_by_signal(signal_id: str, db: Session = Depends(get_db)) -> dict:
    audit = db.execute(
        select(RecommendationAuditLog).where(RecommendationAuditLog.signal_id == signal_id).order_by(desc(RecommendationAuditLog.created_at)).limit(1)
    ).scalars().first()
    if audit is None:
        raise HTTPException(status_code=404, detail="Recommendation audit not found")
    return _audit_to_dict(audit)


@router.get("/trade-plans/{signal_id}", tags=["recommendations"])
def trade_plan(signal_id: str, db: Session = Depends(get_db)) -> dict:
    audit = db.execute(
        select(RecommendationAuditLog).where(RecommendationAuditLog.signal_id == signal_id).order_by(desc(RecommendationAuditLog.created_at)).limit(1)
    ).scalars().first()
    if audit is None:
        raise HTTPException(status_code=404, detail="Trade plan not found")
    return audit.risk_plan_json


@router.get("/calendar/{instrument}", tags=["news"])
def calendar(instrument: str) -> list[dict]:
    _validate_instrument(instrument)
    meta = SUPPORTED_INSTRUMENTS[instrument]
    now = datetime.now(UTC)
    return provider.get_events(now - timedelta(hours=1), now + timedelta(hours=24), [meta["base"], meta["quote"]])


@router.get("/news/{instrument}", tags=["news"])
def news(instrument: str) -> list[dict]:
    _validate_instrument(instrument)
    meta = SUPPORTED_INSTRUMENTS[instrument]
    now = datetime.now(UTC)
    return provider.get_news(instrument, [meta["base"], meta["quote"]], now - timedelta(hours=12), now)


@router.get("/news-risk/{instrument}", tags=["news"])
def news_risk(instrument: str) -> dict:
    _validate_instrument(instrument)
    return journal_service.news_engine.assess(instrument).model_dump(mode="json")


@router.post("/backtest/run", tags=["backtest"])
def run_backtest(
    strategy_id: str = Query(default="ema_trend_pullback"),
    instrument: str = Query(default="EUR_USD"),
    timeframe: str = Query(default="H1"),
) -> dict:
    _validate_instrument(instrument)
    _validate_timeframe(timeframe)
    return backtesting_engine.summarize(strategy_id, "1.0.0", instrument, timeframe).model_dump()


@router.get("/backtest/results", tags=["backtest"])
def backtest_results() -> list[dict]:
    return [backtesting_engine.summarize("ema_trend_pullback", "1.0.0", instrument, "H1").model_dump() for instrument in SUPPORTED_INSTRUMENTS]


@router.get("/backtest/summary/{strategy_id}", tags=["backtest"])
def backtest_summary(strategy_id: str, instrument: str = "EUR_USD", timeframe: str = "H1") -> dict:
    _validate_instrument(instrument)
    _validate_timeframe(timeframe)
    return backtesting_engine.summarize(strategy_id, "1.0.0", instrument, timeframe).model_dump()


@router.get("/journal", tags=["journal"])
def journal(
    db: Session = Depends(get_db),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    instrument: str | None = Query(default=None),
    decision: str | None = Query(default=None),
) -> list[dict]:
    stmt = select(RecommendationAuditLog).order_by(desc(RecommendationAuditLog.created_at))
    if instrument:
        _validate_instrument(instrument)
        stmt = stmt.where(RecommendationAuditLog.instrument == instrument)
    if decision:
        stmt = stmt.where(RecommendationAuditLog.final_decision == decision)
    audits = db.execute(stmt.limit(limit).offset(offset)).scalars().all()
    return [_audit_to_dict(audit) for audit in audits]


@router.get("/journal/stats", tags=["journal"])
def journal_stats(db: Session = Depends(get_db)) -> dict:
    total = db.execute(select(func.count(RecommendationAuditLog.id))).scalar() or 0
    no_trade = db.execute(
        select(func.count(RecommendationAuditLog.id)).where(RecommendationAuditLog.final_decision.like("REJECTED%"))
    ).scalar() or 0
    outcomes = db.execute(select(func.count(SignalOutcome.id))).scalar() or 0
    mock_signals = db.execute(select(func.count(StrategySignal.id)).where(StrategySignal.is_mock.is_(True))).scalar() or 0
    return {
        "total_decisions": total,
        "rejected_or_no_trade": no_trade,
        "outcomes_tracked": outcomes,
        "mock_data_rows": mock_signals,
    }


class OutcomeUpdateBody(BaseModel):
    signal_id: str = Field(min_length=1)
    outcome: Literal["tp1_hit_before_sl", "tp2_hit_before_sl", "sl_hit", "expired", "manual_invalidated", "still_open", "ambiguous"]
    ambiguity_reason: str | None = None


@router.post("/journal/outcome/update", tags=["journal"])
def update_outcome(body: Annotated[OutcomeUpdateBody, Body()], db: Session = Depends(get_db)) -> dict:
    row = SignalOutcome(
        signal_id=body.signal_id,
        outcome=body.outcome,
        ambiguous_outcome=body.outcome == "ambiguous",
        ambiguity_reason=body.ambiguity_reason if body.outcome == "ambiguous" else None,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"id": row.id, "signal_id": row.signal_id, "outcome": row.outcome, "ambiguous_outcome": row.ambiguous_outcome}


@router.post("/journal/outcome/track", tags=["journal"])
def track_outcomes(db: Session = Depends(get_db)) -> dict:
    return outcome_tracker.track(db)


@router.get("/audit/{signal_id}", tags=["audit"])
def audit(signal_id: str, db: Session = Depends(get_db)) -> list[dict]:
    rows = db.execute(
        select(RecommendationAuditLog).where(RecommendationAuditLog.signal_id == signal_id).order_by(desc(RecommendationAuditLog.created_at))
    ).scalars().all()
    return [_audit_to_dict(row) for row in rows]


class AlertCreateBody(BaseModel):
    signal_id: str = Field(min_length=1)
    alert_type: str = Field(default="watchlist_setup", min_length=1, max_length=64)


@router.post("/alerts", tags=["alerts"])
def create_alert(body: Annotated[AlertCreateBody, Body()], db: Session = Depends(get_db)) -> dict:
    audit_row = db.execute(
        select(RecommendationAuditLog).where(RecommendationAuditLog.signal_id == body.signal_id).order_by(desc(RecommendationAuditLog.created_at)).limit(1)
    ).scalars().first()
    if audit_row is None:
        raise HTTPException(status_code=404, detail="Signal not found")
    arbiter_decision = audit_row.output_payload_json.get("final_arbiter", {}) if isinstance(audit_row.output_payload_json, dict) else {}
    if not arbiter_decision.get("allowed_to_alert"):
        return {"status": "not_created", "reason": "Arbiter did not allow alert for this signal"}
    alert = Alert(signal_id=body.signal_id, alert_type=body.alert_type, status="created")
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return {"id": alert.id, "signal_id": alert.signal_id, "alert_type": alert.alert_type, "status": alert.status}


@router.get("/alerts", tags=["alerts"])
def alerts(db: Session = Depends(get_db), limit: int = Query(default=100, ge=1, le=500)) -> list[dict]:
    rows = db.execute(select(Alert).order_by(desc(Alert.created_at)).limit(limit)).scalars().all()
    return [{"id": row.id, "signal_id": row.signal_id, "alert_type": row.alert_type, "status": row.status, "created_at": row.created_at.isoformat()} for row in rows]


@router.delete("/alerts/{alert_id}", tags=["alerts"])
def delete_alert(alert_id: str, db: Session = Depends(get_db)) -> dict:
    alert = db.get(Alert, alert_id)
    if alert is None:
        return {"alert_id": alert_id, "status": "not_found"}
    db.delete(alert)
    db.commit()
    return {"alert_id": alert_id, "status": "deleted"}


@router.get("/feature-flags", tags=["admin"])
def feature_flags(db: Session = Depends(get_db)) -> list[dict]:
    rows = db.execute(select(FeatureFlag)).scalars().all()
    if not rows:
        return [{"flag_name": name, "enabled": enabled, "description": name} for name, enabled in get_settings().feature_flags.items()]
    return [{"flag_name": row.flag_name, "enabled": row.enabled, "description": row.description} for row in rows]


class FeatureFlagPatchBody(BaseModel):
    enabled: bool


@router.patch("/feature-flags/{flag_name}", tags=["admin"])
def patch_feature_flag(flag_name: str, body: Annotated[FeatureFlagPatchBody, Body()], db: Session = Depends(get_db)) -> dict:
    row = db.execute(select(FeatureFlag).where(FeatureFlag.flag_name == flag_name)).scalars().first()
    if row is None:
        raise HTTPException(status_code=404, detail="Feature flag not found")
    row.enabled = body.enabled
    db.commit()
    log.info("feature_flag_updated", extra={"flag_name": flag_name, "enabled": body.enabled})
    return {"flag_name": row.flag_name, "enabled": row.enabled}


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
        "input_payload": row.input_payload_json,
        "output_payload": row.output_payload_json,
    }


def _audit_to_recommendation(row: RecommendationAuditLog) -> RecommendationOut:
    """Reconstruct a RecommendationOut from a persisted audit log row."""
    payload = row.output_payload_json if isinstance(row.output_payload_json, dict) else {}
    if not payload:
        raise HTTPException(status_code=500, detail="Audit row is missing serialized recommendation payload")
    payload["audit_id"] = row.id
    return RecommendationOut.model_validate(payload)
