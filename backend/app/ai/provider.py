from __future__ import annotations

from app.constants import ANALYST_PROMPT_VERSION, RISK_REVIEWER_PROMPT_VERSION
from app.schemas import AIAnalysisOut, RankingResultOut, RiskPlanOut, RiskReviewOut, StrategySignalOut


class LLMProvider:
    model_name = "rules_only_llm_stub"

    def generate_structured_analysis(self, signal: StrategySignalOut, ranking: RankingResultOut, risk_plan: RiskPlanOut, news_status: str) -> AIAnalysisOut:
        evidence_ids = [item.evidence_id for item in signal.evidence]
        recommendation_type = ranking.decision if ranking.decision in {"strong_recommendation", "valid_recommendation", "watchlist_only"} else "no_trade"
        decision = "recommend" if recommendation_type in {"strong_recommendation", "valid_recommendation"} else "watchlist" if recommendation_type == "watchlist_only" else "no_trade"
        confidence = "medium_high" if ranking.final_score >= 85 else "medium" if ranking.final_score >= 75 else "low"
        return AIAnalysisOut(
            decision=decision, recommendation_type=recommendation_type, instrument=signal.instrument, direction=signal.direction, score=ranking.final_score,
            confidence_label=confidence, entry={"type": risk_plan.entry_type, "zone_low": risk_plan.entry_low, "zone_high": risk_plan.entry_high},
            stop_loss={"price": risk_plan.stop_loss, "reason": risk_plan.stop_reason}, take_profit={"tp1": risk_plan.tp1, "tp2": risk_plan.tp2, "logic": risk_plan.tp_reason},
            risk_reward={"to_tp1": risk_plan.rr_to_tp1, "to_tp2": risk_plan.rr_to_tp2}, strategy_stack=[signal.strategy_id],
            trade_thesis="Rules-only AI stub summarized deterministic engine output; no numeric values were created by AI.", invalidation=risk_plan.invalidation,
            why_take=[{"text": "Strategy evidence is present and linked to deterministic calculations.", "evidence_ids": evidence_ids[:2]}] if decision == "recommend" else [],
            why_not_take=[{"text": ranking.rejection_reason or "Setup remains below recommendation threshold.", "evidence_ids": evidence_ids[:2]}] if decision != "recommend" else [],
            news_risk=news_status, final_note="Decision-support only. No trade execution.",
        )

    def run_risk_review(self, signal: StrategySignalOut, ranking: RankingResultOut, risk_plan: RiskPlanOut, news_status: str) -> RiskReviewOut:
        evidence_ids = [item.evidence_id for item in signal.evidence]
        warnings: list[str] = []
        rejection = None
        if risk_plan.missed_entry:
            rejection = "Entry is already missed"
        elif risk_plan.stop_loss is None:
            rejection = "Missing stop loss"
        elif risk_plan.tp1 is None:
            rejection = "Missing take profit"
        elif (risk_plan.rr_to_tp1 or 0) < 1.5:
            rejection = "Reward/risk is below 1.5"
        elif news_status == "blackout":
            rejection = "News blackout is active"
        elif ranking.rejection_reason:
            rejection = ranking.rejection_reason
        if signal.is_mock:
            warnings.append("Signal uses MOCK_DATA and cannot be displayed as a live trade recommendation.")
        mode = "trade_recommendation" if rejection is None and ranking.decision in {"strong_recommendation", "valid_recommendation"} else "watchlist" if ranking.decision == "watchlist_only" else "no_trade"
        return RiskReviewOut(risk_review_passed=rejection is None, rejection_reason=rejection, warnings=warnings, recommended_display_mode=mode, evidence_ids_reviewed=evidence_ids)

ANALYST_PROMPT_VERSION_VALUE = ANALYST_PROMPT_VERSION
RISK_REVIEWER_PROMPT_VERSION_VALUE = RISK_REVIEWER_PROMPT_VERSION
