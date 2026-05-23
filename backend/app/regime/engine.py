from __future__ import annotations

from app.schemas import Evidence, FeatureSnapshot, RegimeSnapshotOut


class RegimeEngine:
    def classify(self, features: FeatureSnapshot) -> RegimeSnapshotOut:
        preferred: list[str] = []
        blocked: list[str] = []
        if features.trend_strength >= 35 and features.trend_direction != "neutral":
            preferred.extend(["ema_trend_pullback", "breakout_retest", "macd_momentum_continuation"])
            blocked.append("bollinger_mean_reversion")
        elif features.range_strength >= 60:
            preferred.extend(["bollinger_mean_reversion", "engulfing_at_structure", "rsi_divergence_reversal"])
        if features.volatility_state == "compressed":
            preferred.append("donchian_breakout")
        if features.session_state == "low_liquidity":
            blocked.extend(["asian_range_breakout", "london_continuation"])
        evidence = [Evidence(evidence_id=f"regime:{features.instrument}:{features.timeframe}:trend", text=f"Trend is {features.trend_direction} with strength {features.trend_strength:.1f}.", source="regime_engine")]
        return RegimeSnapshotOut(
            instrument=features.instrument,
            timeframe=features.timeframe,
            trend_state=features.trend_direction if features.trend_direction in {"bullish", "bearish"} else "neutral",
            trend_strength=features.trend_strength,
            range_strength=features.range_strength,
            volatility_state=features.volatility_state,  # type: ignore[arg-type]
            session_state=features.session_state,  # type: ignore[arg-type]
            preferred_strategies=sorted(set(preferred)),
            blocked_strategies=sorted(set(blocked)),
            evidence=evidence,
            data_status=features.data_status,
            is_mock=features.is_mock,
        )
