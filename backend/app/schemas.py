from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

DataStatus = Literal["LIVE", "DELAYED", "MOCK", "STALE", "DEGRADED", "UNAVAILABLE"]
Direction = Literal["long", "short", "none"]

class Evidence(BaseModel):
    evidence_id: str
    text: str
    source: str = "strategy_engine"

class RiskFlag(BaseModel):
    flag_id: str
    text: str

class CandleOut(BaseModel):
    provider: str
    instrument: str
    timeframe: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float | None = None
    complete: bool = True
    data_status: DataStatus
    is_mock: bool

class QuoteOut(BaseModel):
    provider: str
    instrument: str
    timestamp: datetime
    bid: float
    ask: float
    mid: float
    spread: float
    spread_pips: float
    data_status: DataStatus
    is_mock: bool

class DataQualityStatus(BaseModel):
    instrument: str
    data_status: DataStatus
    data_provider: str
    latest_candle_timestamp: datetime | None
    latest_quote_timestamp: datetime | None
    data_quality_passed: bool
    data_quality_rejection_reason: str | None

class FeatureSnapshot(BaseModel):
    instrument: str
    timeframe: str
    timestamp: datetime | None
    ema20: float | None = None
    ema50: float | None = None
    ema200: float | None = None
    sma50: float | None = None
    sma200: float | None = None
    rsi14: float | None = None
    macd: dict[str, float | None]
    atr14: float | None = None
    adx14: float | None = None
    bollinger: dict[str, float | None]
    donchian: dict[str, float | None]
    recent_swing_highs: list[float]
    recent_swing_lows: list[float]
    support_zones: list[float]
    resistance_zones: list[float]
    previous_day_high: float | None = None
    previous_day_low: float | None = None
    previous_week_high: float | None = None
    previous_week_low: float | None = None
    distance_to_support: float | None = None
    distance_to_resistance: float | None = None
    asian_session_range: dict[str, float | None]
    london_session_state: str
    new_york_session_state: str
    london_new_york_overlap: bool
    low_liquidity_period: bool
    atr_percentage: float | None = None
    volatility_compression: bool
    volatility_expansion: bool
    candle_range_relative_to_atr: float | None = None
    current_spread_pips: float | None = None
    spread_threshold_passed: bool
    spread_cost_in_r: float | None = None
    trend_direction: str
    trend_strength: float
    range_strength: float
    volatility_state: str
    session_state: str
    higher_timeframe_bias: str
    breakout_status: str
    pullback_status: str
    liquidity_sweep_status: str
    data_status: DataStatus
    is_mock: bool

class StrategySignalOut(BaseModel):
    id: str | None = None
    strategy_id: str
    strategy_version: str
    strategy_family: str
    instrument: str
    timeframe: str
    trigger_timeframe: str
    direction: Direction
    status: Literal["active", "watchlist", "rejected"]
    entry_zone: dict[str, float | None]
    suggested_stop: float | None
    suggested_targets: list[float | None]
    evidence: list[Evidence]
    risk_flags: list[RiskFlag]
    raw_confidence: float = Field(ge=0, le=100)
    source_candle_timestamp: datetime | None = None
    data_status: DataStatus
    is_mock: bool

    @field_validator("evidence")
    @classmethod
    def evidence_required(cls, value: list[Evidence]) -> list[Evidence]:
        if not value:
            raise ValueError("strategy signals must include evidence ids")
        return value

class RegimeSnapshotOut(BaseModel):
    instrument: str
    timeframe: str
    trend_state: Literal["bullish", "bearish", "neutral"]
    trend_strength: float
    range_strength: float
    volatility_state: Literal["compressed", "normal", "expanding"]
    session_state: Literal["asia", "london", "new_york", "overlap", "low_liquidity"]
    preferred_strategies: list[str]
    blocked_strategies: list[str]
    evidence: list[Evidence]
    data_status: DataStatus
    is_mock: bool

class NewsRiskOut(BaseModel):
    instrument: str
    news_risk_status: Literal["clear", "caution", "blackout", "unavailable"]
    blackout_active: bool
    next_event: dict | None
    headline_sentiment: dict
    evidence: list[Evidence]
    data_status: DataStatus
    is_mock: bool

class ProviderReconciliationOut(BaseModel):
    instrument: str
    timeframe: str
    status: Literal["SINGLE_PROVIDER", "AGREEMENT", "DISAGREEMENT", "UNAVAILABLE"]
    data_status: DataStatus
    providers_checked: list[str]
    max_price_disagreement: float | None
    tolerance: float | None
    rejection_reason: str | None

class CorrelationContextOut(BaseModel):
    instrument: str
    status: Literal["available", "unavailable"]
    correlation_agreement: Literal["supportive", "conflicting", "neutral", "unavailable"]
    summary: str
    evidence: list[Evidence]

class RankingResultOut(BaseModel):
    signal_id: str | None
    ranking_version: str
    final_score: float
    score_breakdown: dict[str, float]
    decision: Literal["strong_recommendation", "valid_recommendation", "watchlist_only", "weak_setup", "no_trade"]
    rejection_reason: str | None

class RiskPlanOut(BaseModel):
    risk_engine_version: str
    entry_type: Literal["limit_retest", "confirmation_entry", "breakout_entry", "watchlist_trigger", "none"]
    entry_low: float | None
    entry_high: float | None
    stop_loss: float | None
    tp1: float | None
    tp2: float | None
    rr_to_tp1: float | None
    rr_to_tp2: float | None
    invalidation: str
    stop_reason: str
    tp_reason: str
    entry_valid_until: datetime | None
    valid_for_candles: int | None
    missed_entry: bool
    cost_in_r: float | None
    rejection_reason: str | None = None

class AIAnalysisOut(BaseModel):
    decision: Literal["recommend", "watchlist", "no_trade"]
    recommendation_type: Literal["strong_recommendation", "valid_recommendation", "watchlist_only", "no_trade"]
    instrument: str
    direction: Direction
    score: float
    confidence_label: Literal["low", "medium", "medium_high", "high"]
    entry: dict
    stop_loss: dict
    take_profit: dict
    risk_reward: dict
    strategy_stack: list[str]
    trade_thesis: str
    invalidation: str
    why_take: list[dict]
    why_not_take: list[dict]
    news_risk: Literal["clear", "caution", "blackout", "unavailable"]
    final_note: str = "Decision-support only. No trade execution."

class RiskReviewOut(BaseModel):
    risk_review_passed: bool
    rejection_reason: str | None
    warnings: list[str]
    recommended_display_mode: Literal["trade_recommendation", "watchlist", "no_trade"]
    evidence_ids_reviewed: list[str]

class ArbiterDecisionOut(BaseModel):
    arbiter_version: str
    final_decision: str
    display_mode: Literal["trade_recommendation", "watchlist", "no_trade"]
    allowed_to_alert: bool
    rejection_reason: str | None
    audit_required: bool = True

class RecommendationOut(BaseModel):
    signal_id: str
    instrument: str
    data_status: DataStatus
    data_provider: str
    latest_candle_timestamp: datetime | None
    latest_quote_timestamp: datetime | None
    data_quality_passed: bool
    data_quality_rejection_reason: str | None
    strategy_signal: StrategySignalOut
    regime: RegimeSnapshotOut
    news_risk: NewsRiskOut
    reconciliation: ProviderReconciliationOut
    correlation_context: CorrelationContextOut
    ranking: RankingResultOut
    risk_plan: RiskPlanOut
    ai_analysis: AIAnalysisOut
    risk_review: RiskReviewOut
    final_arbiter: ArbiterDecisionOut
    no_trade_explanation: dict[str, list[str] | bool]
    audit_id: str | None = None
    is_mock: bool

class HealthOut(BaseModel):
    status: Literal["healthy", "degraded"]
    service: str
    mock_data_enabled: bool
    live_recommendations_enabled: bool
    feature_flags: dict[str, bool]
    checks: dict[str, str]

class BacktestSummaryOut(BaseModel):
    strategy_id: str
    strategy_version: str
    instrument: str
    timeframe: str
    sample_size: int
    win_rate: float | None
    average_r: float | None
    expected_r: float | None
    profit_factor: float | None
    max_drawdown_r: float | None
    average_adverse_excursion_r: float | None
    average_favorable_excursion_r: float | None
    average_time_in_trade_minutes: float | None
    confidence_penalty: float
    status: str
