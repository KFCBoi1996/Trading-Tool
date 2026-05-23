from __future__ import annotations

from app.constants import ARBITER_VERSION, BLOCKING_DATA_STATUSES
from app.schemas import ArbiterDecisionOut, NewsRiskOut, RankingResultOut, RiskPlanOut, RiskReviewOut


class FinalArbiter:
    def decide(self, data_status: str, data_quality_passed: bool, news_risk: NewsRiskOut, ranking: RankingResultOut, risk_plan: RiskPlanOut, risk_review: RiskReviewOut, feature_flags: dict[str, bool]) -> ArbiterDecisionOut:
        decision = ranking.decision.upper()
        rejection = ranking.rejection_reason
        display_mode = "trade_recommendation" if ranking.decision in {"strong_recommendation", "valid_recommendation"} else "watchlist" if ranking.decision == "watchlist_only" else "no_trade"
        if not data_quality_passed:
            decision, display_mode, rejection = "REJECTED_DATA_QUALITY", "no_trade", rejection or "Data quality failed"
        elif data_status in BLOCKING_DATA_STATUSES:
            decision, display_mode, rejection = ("REJECTED_STALE" if data_status == "STALE" else "REJECTED_DATA_QUALITY"), "no_trade", f"Data status {data_status} blocks recommendations"
        elif news_risk.blackout_active:
            decision, display_mode, rejection = "REJECTED_NEWS_BLACKOUT", "no_trade", "High-impact news blackout is active"
        elif risk_plan.rejection_reason and "spread" in risk_plan.rejection_reason.lower():
            decision, display_mode, rejection = "REJECTED_SPREAD", "no_trade", risk_plan.rejection_reason
        elif risk_plan.rejection_reason and "reward/risk" in risk_plan.rejection_reason.lower():
            decision, display_mode, rejection = "REJECTED_RR", "no_trade", risk_plan.rejection_reason
        elif risk_plan.missed_entry:
            decision, display_mode, rejection = "REJECTED_MISSED_ENTRY", "no_trade", "Entry is already missed"
        elif not risk_review.risk_review_passed:
            decision, display_mode, rejection = "REJECTED_AI_REVIEW", "no_trade", risk_review.rejection_reason
        elif not feature_flags.get("LIVE_RECOMMENDATIONS_ENABLED", False) or feature_flags.get("PAPER_VALIDATION_MODE_ENABLED", False):
            decision, display_mode, rejection = "WATCHLIST_ONLY", "watchlist", "Live recommendations are disabled or paper validation mode is active"
        allowed_to_alert = display_mode != "no_trade" and feature_flags.get("ALERTS_ENABLED", False) and not feature_flags.get("PAPER_VALIDATION_MODE_ENABLED", False)
        return ArbiterDecisionOut(arbiter_version=ARBITER_VERSION, final_decision=decision, display_mode=display_mode, allowed_to_alert=allowed_to_alert, rejection_reason=rejection, audit_required=True)
