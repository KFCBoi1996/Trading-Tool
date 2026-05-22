from __future__ import annotations

from app.arbiter.final_arbiter import FinalArbiter
from app.schemas import NewsRiskOut, RankingResultOut, RiskPlanOut, RiskReviewOut


def test_final_arbiter_blocks_mock_data():
    news = NewsRiskOut(instrument="EUR_USD", news_risk_status="clear", blackout_active=False, next_event=None, headline_sentiment={"directional_bias": "neutral"}, evidence=[], data_status="MOCK", is_mock=True)
    ranking = RankingResultOut(signal_id="s", ranking_version="v", final_score=90, score_breakdown={}, decision="strong_recommendation", rejection_reason=None)
    risk = RiskPlanOut(risk_engine_version="v", entry_type="limit_retest", entry_low=1.0, entry_high=1.1, stop_loss=0.9, tp1=1.3, tp2=1.4, rr_to_tp1=2.0, rr_to_tp2=3.0, invalidation="x", stop_reason="x", tp_reason="x", entry_valid_until=None, valid_for_candles=3, missed_entry=False, cost_in_r=0.1)
    review = RiskReviewOut(risk_review_passed=True, rejection_reason=None, warnings=[], recommended_display_mode="trade_recommendation", evidence_ids_reviewed=[])
    decision = FinalArbiter().decide("MOCK", True, news, ranking, risk, review, {"LIVE_RECOMMENDATIONS_ENABLED": True, "PAPER_VALIDATION_MODE_ENABLED": False, "ALERTS_ENABLED": True})
    assert decision.display_mode == "no_trade"
    assert decision.final_decision == "REJECTED_DATA_QUALITY"
