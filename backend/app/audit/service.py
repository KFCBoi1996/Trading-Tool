from __future__ import annotations

from sqlalchemy.orm import Session
from app.constants import ANALYST_PROMPT_VERSION, ARBITER_VERSION, RISK_REVIEWER_PROMPT_VERSION
from app.db.models import RecommendationAuditLog
from app.schemas import RecommendationOut

class AuditService:
    def record(self, db: Session, recommendation: RecommendationOut) -> str:
        row = RecommendationAuditLog(
            signal_id=recommendation.signal_id,
            instrument=recommendation.instrument,
            final_decision=recommendation.final_arbiter.final_decision,
            rejection_reason=recommendation.final_arbiter.rejection_reason,
            data_snapshot_timestamp=recommendation.latest_candle_timestamp,
            data_status=recommendation.data_status,
            data_provider=recommendation.data_provider,
            strategy_id=recommendation.strategy_signal.strategy_id,
            strategy_version=recommendation.strategy_signal.strategy_version,
            ranking_version=recommendation.ranking.ranking_version,
            risk_engine_version=recommendation.risk_plan.risk_engine_version,
            arbiter_version=ARBITER_VERSION,
            ai_model="rules_only_llm_stub",
            analyst_prompt_version=ANALYST_PROMPT_VERSION,
            risk_reviewer_prompt_version=RISK_REVIEWER_PROMPT_VERSION,
            input_payload_json={"strategy_signal": recommendation.strategy_signal.model_dump(mode="json"), "data_quality": recommendation.data_quality_passed},
            output_payload_json={"final_arbiter": recommendation.final_arbiter.model_dump(mode="json")},
            score_breakdown_json=recommendation.ranking.score_breakdown,
            risk_plan_json=recommendation.risk_plan.model_dump(mode="json"),
            news_risk_json=recommendation.news_risk.model_dump(mode="json"),
            regime_snapshot_json=recommendation.regime.model_dump(mode="json"),
            ai_review_json=recommendation.ai_analysis.model_dump(mode="json"),
            risk_review_json=recommendation.risk_review.model_dump(mode="json"),
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        return row.id
