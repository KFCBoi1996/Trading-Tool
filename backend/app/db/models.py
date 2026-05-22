from __future__ import annotations

import uuid
from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from .session import Base

def now_utc() -> datetime:
    return datetime.now(timezone.utc)

def uuid_str() -> str:
    return str(uuid.uuid4())

class Instrument(Base):
    __tablename__ = "instruments"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uuid_str)
    symbol: Mapped[str] = mapped_column(String(16), unique=True, nullable=False, index=True)
    base_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    quote_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    pip_size: Mapped[float] = mapped_column(Float, nullable=False)
    price_precision: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, onupdate=now_utc, nullable=False)

class Candle(Base):
    __tablename__ = "candles"
    __table_args__ = (
        UniqueConstraint("provider", "instrument", "timeframe", "timestamp", name="uq_candles_provider_instrument_timeframe_timestamp"),
        Index("ix_candles_instrument_timeframe_timestamp", "instrument", "timeframe", "timestamp"),
    )
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uuid_str)
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    instrument: Mapped[str] = mapped_column(String(16), nullable=False)
    timeframe: Mapped[str] = mapped_column(String(8), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    open: Mapped[float] = mapped_column(Float, nullable=False)
    high: Mapped[float] = mapped_column(Float, nullable=False)
    low: Mapped[float] = mapped_column(Float, nullable=False)
    close: Mapped[float] = mapped_column(Float, nullable=False)
    volume: Mapped[float | None] = mapped_column(Float)
    complete: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    data_status: Mapped[str] = mapped_column(String(16), nullable=False)
    is_mock: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)

class Quote(Base):
    __tablename__ = "quotes"
    __table_args__ = (Index("ix_quotes_instrument_timestamp", "instrument", "timestamp"),)
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uuid_str)
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    instrument: Mapped[str] = mapped_column(String(16), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    bid: Mapped[float] = mapped_column(Float, nullable=False)
    ask: Mapped[float] = mapped_column(Float, nullable=False)
    mid: Mapped[float] = mapped_column(Float, nullable=False)
    spread: Mapped[float] = mapped_column(Float, nullable=False)
    spread_pips: Mapped[float] = mapped_column(Float, nullable=False)
    data_status: Mapped[str] = mapped_column(String(16), nullable=False)
    is_mock: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)

class EconomicEvent(Base):
    __tablename__ = "economic_events"
    __table_args__ = (Index("ix_economic_events_currency_event_time", "currency", "event_time"),)
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uuid_str)
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    event_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    country: Mapped[str] = mapped_column(String(64), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    event_name: Mapped[str] = mapped_column(String(255), nullable=False)
    importance: Mapped[str] = mapped_column(String(16), nullable=False)
    actual: Mapped[str | None] = mapped_column(String(64))
    forecast: Mapped[str | None] = mapped_column(String(64))
    previous: Mapped[str | None] = mapped_column(String(64))
    data_status: Mapped[str] = mapped_column(String(16), nullable=False)
    is_mock: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)

class NewsItem(Base):
    __tablename__ = "news_items"
    __table_args__ = (Index("ix_news_items_published_at", "published_at"),)
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uuid_str)
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source: Mapped[str] = mapped_column(String(128), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    url: Mapped[str | None] = mapped_column(String(512))
    affected_currencies: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    sentiment_score: Mapped[float | None] = mapped_column(Float)
    relevance_score: Mapped[float | None] = mapped_column(Float)
    data_status: Mapped[str] = mapped_column(String(16), nullable=False)
    is_mock: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)

class StrategyDefinition(Base):
    __tablename__ = "strategy_definitions"
    __table_args__ = (Index("ix_strategy_definitions_strategy_version", "strategy_id", "strategy_version"),)
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uuid_str)
    strategy_id: Mapped[str] = mapped_column(String(128), nullable=False)
    strategy_version: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    family: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    parameters_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, onupdate=now_utc, nullable=False)

class StrategySignal(Base):
    __tablename__ = "strategy_signals"
    __table_args__ = (
        Index("ix_strategy_signals_instrument_created_at", "instrument", "created_at"),
        Index("ix_strategy_signals_strategy_version", "strategy_id", "strategy_version"),
    )
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uuid_str)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)
    instrument: Mapped[str] = mapped_column(String(16), nullable=False)
    timeframe: Mapped[str] = mapped_column(String(8), nullable=False)
    trigger_timeframe: Mapped[str] = mapped_column(String(8), nullable=False)
    strategy_id: Mapped[str] = mapped_column(String(128), nullable=False)
    strategy_version: Mapped[str] = mapped_column(String(32), nullable=False)
    strategy_family: Mapped[str] = mapped_column(String(64), nullable=False)
    direction: Mapped[str] = mapped_column(String(8), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    entry_low: Mapped[float | None] = mapped_column(Float)
    entry_high: Mapped[float | None] = mapped_column(Float)
    suggested_stop: Mapped[float | None] = mapped_column(Float)
    suggested_tp1: Mapped[float | None] = mapped_column(Float)
    suggested_tp2: Mapped[float | None] = mapped_column(Float)
    raw_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    evidence_json: Mapped[list[dict]] = mapped_column(JSON, default=list, nullable=False)
    risk_flags_json: Mapped[list[dict]] = mapped_column(JSON, default=list, nullable=False)
    source_candle_timestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    data_status: Mapped[str] = mapped_column(String(16), nullable=False)
    is_mock: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

class RegimeSnapshot(Base):
    __tablename__ = "regime_snapshots"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uuid_str)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)
    instrument: Mapped[str] = mapped_column(String(16), nullable=False)
    timeframe: Mapped[str] = mapped_column(String(8), nullable=False)
    trend_state: Mapped[str] = mapped_column(String(16), nullable=False)
    trend_strength: Mapped[float] = mapped_column(Float, nullable=False)
    range_strength: Mapped[float] = mapped_column(Float, nullable=False)
    volatility_state: Mapped[str] = mapped_column(String(32), nullable=False)
    session_state: Mapped[str] = mapped_column(String(32), nullable=False)
    preferred_strategies_json: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    blocked_strategies_json: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    data_status: Mapped[str] = mapped_column(String(16), nullable=False)
    is_mock: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

class RankedSetup(Base):
    __tablename__ = "ranked_setups"
    __table_args__ = (Index("ix_ranked_setups_decision_created_at", "decision", "created_at"),)
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uuid_str)
    signal_id: Mapped[str] = mapped_column(String, ForeignKey("strategy_signals.id"), nullable=False, index=True)
    ranking_version: Mapped[str] = mapped_column(String(64), nullable=False)
    final_score: Mapped[float] = mapped_column(Float, nullable=False)
    score_breakdown_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    decision: Mapped[str] = mapped_column(String(64), nullable=False)
    rejection_reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)

class TradePlan(Base):
    __tablename__ = "trade_plans"
    __table_args__ = (Index("ix_trade_plans_signal_id", "signal_id"),)
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uuid_str)
    signal_id: Mapped[str] = mapped_column(String, ForeignKey("strategy_signals.id"), nullable=False)
    ranked_setup_id: Mapped[str | None] = mapped_column(String, ForeignKey("ranked_setups.id"))
    risk_engine_version: Mapped[str] = mapped_column(String(64), nullable=False)
    instrument: Mapped[str] = mapped_column(String(16), nullable=False)
    direction: Mapped[str] = mapped_column(String(8), nullable=False)
    entry_type: Mapped[str] = mapped_column(String(32), nullable=False)
    entry_low: Mapped[float | None] = mapped_column(Float)
    entry_high: Mapped[float | None] = mapped_column(Float)
    stop_loss: Mapped[float | None] = mapped_column(Float)
    tp1: Mapped[float | None] = mapped_column(Float)
    tp2: Mapped[float | None] = mapped_column(Float)
    rr_to_tp1: Mapped[float | None] = mapped_column(Float)
    rr_to_tp2: Mapped[float | None] = mapped_column(Float)
    invalidation: Mapped[str] = mapped_column(Text, nullable=False)
    stop_reason: Mapped[str] = mapped_column(Text, nullable=False)
    tp_reason: Mapped[str] = mapped_column(Text, nullable=False)
    entry_valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    valid_for_candles: Mapped[int | None] = mapped_column(Integer)
    missed_entry: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)

class AIReview(Base):
    __tablename__ = "ai_reviews"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uuid_str)
    signal_id: Mapped[str] = mapped_column(String, ForeignKey("strategy_signals.id"), nullable=False)
    ranked_setup_id: Mapped[str | None] = mapped_column(String, ForeignKey("ranked_setups.id"))
    review_type: Mapped[str] = mapped_column(String(32), nullable=False)
    ai_model: Mapped[str] = mapped_column(String(64), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(64), nullable=False)
    passed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    decision: Mapped[str] = mapped_column(String(64), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    why_take_json: Mapped[list[dict]] = mapped_column(JSON, default=list, nullable=False)
    why_not_take_json: Mapped[list[dict]] = mapped_column(JSON, default=list, nullable=False)
    warnings_json: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    evidence_ids_json: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    raw_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)

class SignalOutcome(Base):
    __tablename__ = "signal_outcomes"
    __table_args__ = (Index("ix_signal_outcomes_signal_id", "signal_id"),)
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uuid_str)
    signal_id: Mapped[str] = mapped_column(String, ForeignKey("strategy_signals.id"), nullable=False)
    outcome: Mapped[str] = mapped_column(String(64), nullable=False)
    realized_r: Mapped[float | None] = mapped_column(Float)
    mfe_r: Mapped[float | None] = mapped_column(Float)
    mae_r: Mapped[float | None] = mapped_column(Float)
    time_to_outcome_minutes: Mapped[int | None] = mapped_column(Integer)
    ambiguous_outcome: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ambiguity_reason: Mapped[str | None] = mapped_column(Text)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)

class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uuid_str)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)

class Watchlist(Base):
    __tablename__ = "watchlists"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uuid_str)
    user_id: Mapped[str | None] = mapped_column(String, ForeignKey("users.id"))
    instrument: Mapped[str] = mapped_column(String(16), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)

class Alert(Base):
    __tablename__ = "alerts"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uuid_str)
    user_id: Mapped[str | None] = mapped_column(String, ForeignKey("users.id"))
    signal_id: Mapped[str | None] = mapped_column(String, ForeignKey("strategy_signals.id"))
    alert_type: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)

class RecommendationAuditLog(Base):
    __tablename__ = "recommendation_audit_log"
    __table_args__ = (
        Index("ix_recommendation_audit_log_signal_id", "signal_id"),
        Index("ix_recommendation_audit_log_created_at", "created_at"),
        Index("ix_recommendation_audit_log_decision_created_at", "final_decision", "created_at"),
    )
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uuid_str)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)
    signal_id: Mapped[str | None] = mapped_column(String, nullable=True)
    instrument: Mapped[str] = mapped_column(String(16), nullable=False)
    final_decision: Mapped[str] = mapped_column(String(64), nullable=False)
    rejection_reason: Mapped[str | None] = mapped_column(Text)
    data_snapshot_timestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    data_status: Mapped[str] = mapped_column(String(16), nullable=False)
    data_provider: Mapped[str] = mapped_column(String(64), nullable=False)
    strategy_id: Mapped[str | None] = mapped_column(String(128))
    strategy_version: Mapped[str | None] = mapped_column(String(32))
    ranking_version: Mapped[str | None] = mapped_column(String(64))
    risk_engine_version: Mapped[str | None] = mapped_column(String(64))
    arbiter_version: Mapped[str] = mapped_column(String(64), nullable=False)
    ai_model: Mapped[str | None] = mapped_column(String(64))
    analyst_prompt_version: Mapped[str | None] = mapped_column(String(64))
    risk_reviewer_prompt_version: Mapped[str | None] = mapped_column(String(64))
    input_payload_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    output_payload_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    score_breakdown_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    risk_plan_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    news_risk_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    regime_snapshot_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    ai_review_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    risk_review_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

class SystemHealthEvent(Base):
    __tablename__ = "system_health_events"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uuid_str)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)
    service_name: Mapped[str] = mapped_column(String(64), nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

class FeatureFlag(Base):
    __tablename__ = "feature_flags"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uuid_str)
    flag_name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, onupdate=now_utc, nullable=False)
