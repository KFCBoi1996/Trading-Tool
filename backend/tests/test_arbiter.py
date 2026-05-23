from __future__ import annotations

from app.arbiter.final_arbiter import FinalArbiter
from app.schemas import NewsRiskOut, RankingResultOut, RiskPlanOut, RiskReviewOut


def _ok_news() -> NewsRiskOut:
    return NewsRiskOut(
        instrument="EUR_USD",
        news_risk_status="clear",
        blackout_active=False,
        next_event=None,
        headline_sentiment={"directional_bias": "neutral", "confidence": 0.0, "summary": ""},
        evidence=[],
        data_status="LIVE",
        is_mock=False,
    )


def _ok_ranking() -> RankingResultOut:
    return RankingResultOut(
        signal_id="s",
        ranking_version="v",
        final_score=90,
        score_breakdown={},
        decision="strong_recommendation",
        rejection_reason=None,
    )


def _ok_plan() -> RiskPlanOut:
    return RiskPlanOut(
        risk_engine_version="v",
        entry_type="limit_retest",
        entry_low=1.0,
        entry_high=1.1,
        stop_loss=0.9,
        tp1=1.3,
        tp2=1.4,
        rr_to_tp1=2.0,
        rr_to_tp2=3.0,
        invalidation="x",
        stop_reason="x",
        tp_reason="x",
        entry_valid_until=None,
        valid_for_candles=3,
        missed_entry=False,
        cost_in_r=0.1,
    )


def _ok_review() -> RiskReviewOut:
    return RiskReviewOut(
        risk_review_passed=True,
        rejection_reason=None,
        warnings=[],
        recommended_display_mode="trade_recommendation",
        evidence_ids_reviewed=[],
    )


def _flags(live: bool = True, paper: bool = False) -> dict[str, bool]:
    return {"LIVE_RECOMMENDATIONS_ENABLED": live, "PAPER_VALIDATION_MODE_ENABLED": paper, "ALERTS_ENABLED": True}


def test_arbiter_blocks_mock_data() -> None:
    news = _ok_news().model_copy(update={"data_status": "MOCK", "is_mock": True})
    decision = FinalArbiter().decide("MOCK", True, news, _ok_ranking(), _ok_plan(), _ok_review(), _flags())
    assert decision.display_mode == "no_trade"
    assert decision.final_decision.startswith("REJECTED")


def test_arbiter_blocks_news_blackout() -> None:
    news = _ok_news().model_copy(update={"news_risk_status": "blackout", "blackout_active": True})
    decision = FinalArbiter().decide("LIVE", True, news, _ok_ranking(), _ok_plan(), _ok_review(), _flags())
    assert decision.final_decision == "REJECTED_NEWS_BLACKOUT"


def test_arbiter_blocks_paper_validation_recommendations() -> None:
    decision = FinalArbiter().decide("LIVE", True, _ok_news(), _ok_ranking(), _ok_plan(), _ok_review(), _flags(paper=True))
    assert decision.display_mode == "watchlist"
    assert decision.allowed_to_alert is False


def test_arbiter_allows_live_recommendation_when_all_gates_pass() -> None:
    decision = FinalArbiter().decide("LIVE", True, _ok_news(), _ok_ranking(), _ok_plan(), _ok_review(), _flags())
    assert decision.display_mode == "trade_recommendation"
    assert decision.allowed_to_alert is True
