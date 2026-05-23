from __future__ import annotations

from app.constants import BLOCKING_DATA_STATUSES, MINIMUM_REWARD_RISK, RANKING_VERSION
from app.schemas import NewsRiskOut, RankingResultOut, RegimeSnapshotOut, RiskPlanOut, StrategySignalOut


class RankingEngine:
    def rank(self, signal: StrategySignalOut, regime: RegimeSnapshotOut, news_risk: NewsRiskOut, risk_plan: RiskPlanOut, data_quality_passed: bool) -> RankingResultOut:
        breakdown = {
            "regime_fit": 100.0 if signal.strategy_id in regime.preferred_strategies else 65.0 if not regime.blocked_strategies else 45.0,
            "multi_timeframe_alignment": 80.0 if signal.direction != "none" and regime.trend_state in {"bullish", "bearish"} else 50.0,
            "historical_strategy_edge": 45.0,
            "reward_risk_quality": min(100.0, (risk_plan.rr_to_tp1 or 0.0) / 2.5 * 100),
            "structure_quality": 75.0 if signal.entry_zone.get("low") is not None and signal.suggested_stop is not None else 0.0,
            "volatility_quality": 80.0 if regime.volatility_state != "compressed" else 60.0,
            "news_calendar_safety": 100.0 if news_risk.news_risk_status == "clear" else 40.0 if news_risk.news_risk_status == "caution" else 0.0,
            "spread_liquidity_quality": 100.0 if not signal.risk_flags else 65.0,
        }
        final_score = (
            breakdown["regime_fit"] * 0.20 + breakdown["multi_timeframe_alignment"] * 0.15 + breakdown["historical_strategy_edge"] * 0.15 +
            breakdown["reward_risk_quality"] * 0.15 + breakdown["structure_quality"] * 0.10 + breakdown["volatility_quality"] * 0.10 +
            breakdown["news_calendar_safety"] * 0.10 + breakdown["spread_liquidity_quality"] * 0.05
        )
        rejection = None
        if not data_quality_passed:
            rejection = "Data quality failed"
        elif signal.data_status in BLOCKING_DATA_STATUSES:
            rejection = f"Data status {signal.data_status} blocks recommendations"
        elif news_risk.blackout_active:
            rejection = "High-impact news blackout is active"
        elif risk_plan.stop_loss is None:
            rejection = "Missing stop loss"
        elif risk_plan.tp1 is None:
            rejection = "Missing take profit"
        elif (risk_plan.rr_to_tp1 or 0) < MINIMUM_REWARD_RISK:
            rejection = "Reward/risk is below 1.5"
        elif risk_plan.missed_entry:
            rejection = "Entry is already missed"
        elif risk_plan.rejection_reason:
            rejection = risk_plan.rejection_reason
        if rejection:
            return RankingResultOut(signal_id=signal.id, ranking_version=RANKING_VERSION, final_score=min(final_score, 49.0), score_breakdown=breakdown, decision="no_trade", rejection_reason=rejection)
        if final_score >= 85:
            decision = "strong_recommendation"
        elif final_score >= 75:
            decision = "valid_recommendation"
        elif final_score >= 65:
            decision = "watchlist_only"
        elif final_score >= 50:
            decision = "weak_setup"
        else:
            decision = "no_trade"
        return RankingResultOut(signal_id=signal.id, ranking_version=RANKING_VERSION, final_score=round(final_score, 2), score_breakdown=breakdown, decision=decision, rejection_reason=None if decision != "no_trade" else "Score below threshold")
