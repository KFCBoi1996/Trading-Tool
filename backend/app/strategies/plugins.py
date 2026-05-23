from __future__ import annotations

from app.schemas import Evidence, RiskFlag, StrategySignalOut

from .base import BaseStrategy, StrategyContext


class RuleStrategy(BaseStrategy):
    strategy_id = "base_rule"
    family = "generic"
    description = "Generic deterministic rule strategy"
    parameters = {"min_confidence": 55}

    def _direction(self, context: StrategyContext) -> str:
        if context.setup_features.trend_direction == "bullish":
            return "long"
        if context.setup_features.trend_direction == "bearish":
            return "short"
        return "none"

    def _levels(self, context: StrategyContext, direction: str) -> tuple[dict[str, float | None], float | None, list[float | None]]:
        quote = context.quote.mid
        atr = context.setup_features.atr14 or abs(quote) * 0.001
        if direction == "long":
            low = quote - atr * 0.25
            high = quote + atr * 0.1
            stop = min(context.setup_features.recent_swing_lows or [quote - atr]) - atr * 0.2
            risk = max(high - stop, atr * 0.6)
            return {"low": low, "high": high}, stop, [high + risk * 1.6, high + risk * 2.2]
        if direction == "short":
            low = quote - atr * 0.1
            high = quote + atr * 0.25
            stop = max(context.setup_features.recent_swing_highs or [quote + atr]) + atr * 0.2
            risk = max(stop - low, atr * 0.6)
            return {"low": low, "high": high}, stop, [low - risk * 1.6, low - risk * 2.2]
        return {"low": None, "high": None}, None, [None, None]

    def _status(self, context: StrategyContext, direction: str) -> str:
        if direction == "none" or context.news_risk.blackout_active:
            return "rejected"
        if self.strategy_id in context.regime.blocked_strategies:
            return "watchlist"
        return "active"

    def evaluate(self, context: StrategyContext) -> StrategySignalOut:
        direction = self._direction(context)
        entry_zone, stop, targets = self._levels(context, direction)
        confidence = min(100.0, 45.0 + context.setup_features.trend_strength * 0.55)
        if context.regime.range_strength > 60 and self.family in {"mean_reversion", "reversal", "structure"}:
            confidence += 10
        if self.strategy_id in context.regime.preferred_strategies:
            confidence += 8
        risk_flags: list[RiskFlag] = []
        if context.news_risk.news_risk_status != "clear":
            risk_flags.append(RiskFlag(flag_id="news_risk", text=f"News/calendar status is {context.news_risk.news_risk_status}."))
        if not context.setup_features.spread_threshold_passed:
            risk_flags.append(RiskFlag(flag_id="spread", text="Current spread exceeds pair threshold."))
        return StrategySignalOut(
            strategy_id=self.strategy_id,
            strategy_version=self.strategy_version,
            strategy_family=self.family,
            instrument=context.instrument,
            timeframe=context.setup_timeframe,
            trigger_timeframe=context.trigger_timeframe,
            direction=direction,  # type: ignore[arg-type]
            status=self._status(context, direction),
            entry_zone=entry_zone,
            suggested_stop=stop,
            suggested_targets=targets,
            evidence=[
                Evidence(
                    evidence_id=f"strategy:{self.strategy_id}:trigger",
                    text=f"{self.description} evaluated with deterministic feature inputs.",
                    source="strategy_engine",
                ),
                Evidence(
                    evidence_id=f"strategy:{self.strategy_id}:regime",
                    text=f"Regime preference list: {', '.join(context.regime.preferred_strategies) or 'none'}.",
                    source="regime_engine",
                ),
            ],
            risk_flags=risk_flags,
            raw_confidence=max(0.0, min(100.0, confidence)),
            source_candle_timestamp=context.setup_features.timestamp,
            data_status=context.setup_features.data_status,
            is_mock=context.setup_features.is_mock,
        )

class EMATrendPullback(RuleStrategy):
    strategy_id = "ema_trend_pullback"
    family = "trend_following"
    description = "EMA trend pullback with trigger candle confirmation"

class BreakoutRetest(RuleStrategy):
    strategy_id = "breakout_retest"
    family = "breakout"
    description = "Breakout and retest of prior support/resistance"

class AsianRangeBreakout(RuleStrategy):
    strategy_id = "asian_range_breakout"
    family = "session_breakout"
    description = "London breakout from Asian session range"

class LondonContinuation(RuleStrategy):
    strategy_id = "london_continuation"
    family = "trend_following"
    description = "London session continuation after controlled pullback"

class RSIDivergenceReversal(RuleStrategy):
    strategy_id = "rsi_divergence_reversal"
    family = "reversal"
    description = "RSI divergence reversal near structure"

class MACDMomentumContinuation(RuleStrategy):
    strategy_id = "macd_momentum_continuation"
    family = "momentum"
    description = "MACD momentum continuation with higher timeframe alignment"

class BollingerMeanReversion(RuleStrategy):
    strategy_id = "bollinger_mean_reversion"
    family = "mean_reversion"
    description = "Bollinger Band mean reversion in range-bound conditions"

class DonchianBreakout(RuleStrategy):
    strategy_id = "donchian_breakout"
    family = "breakout"
    description = "Donchian channel breakout with volatility confirmation"

class ADXTrendStrengthFilter(RuleStrategy):
    strategy_id = "adx_trend_strength_filter"
    family = "filter"
    description = "ADX trend strength filter signal"

class EngulfingAtStructure(RuleStrategy):
    strategy_id = "engulfing_at_structure"
    family = "structure"
    description = "Engulfing candle at support or resistance"

class LiquiditySweepReversal(RuleStrategy):
    strategy_id = "liquidity_sweep_reversal"
    family = "reversal"
    description = "Liquidity sweep and range reclaim reversal"

class MultiTimeframeAlignment(RuleStrategy):
    strategy_id = "multi_timeframe_alignment"
    family = "filter"
    description = "H4/H1/M15 directional alignment filter"

STRATEGIES: list[type[BaseStrategy]] = [
    EMATrendPullback,
    BreakoutRetest,
    AsianRangeBreakout,
    LondonContinuation,
    RSIDivergenceReversal,
    MACDMomentumContinuation,
    BollingerMeanReversion,
    DonchianBreakout,
    ADXTrendStrengthFilter,
    EngulfingAtStructure,
    LiquiditySweepReversal,
    MultiTimeframeAlignment,
]

def get_strategy_instances() -> list[BaseStrategy]:
    return [strategy() for strategy in STRATEGIES]
