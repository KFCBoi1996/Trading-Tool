from __future__ import annotations

from sqlalchemy.orm import Session

from app.constants import ANALYST_PROMPT_VERSION, ARBITER_VERSION, RISK_REVIEWER_PROMPT_VERSION
from app.db.models import RecommendationAuditLog
from app.observability import get_logger
from app.schemas import RecommendationOut

log = get_logger("app.audit")


class AuditService:
    def record(self, db: Session, recommendation: RecommendationOut) -> str:
        recommendation_payload = recommendation.model_dump(mode="json")
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
            input_payload_json={
                "strategy_signal": recommendation.strategy_signal.model_dump(mode="json"),
                "data_quality_passed": recommendation.data_quality_passed,
                "data_quality_rejection_reason": recommendation.data_quality_rejection_reason,
                "regime": recommendation.regime.model_dump(mode="json"),
                "reconciliation": recommendation.reconciliation.model_dump(mode="json"),
                "correlation_context": recommendation.correlation_context.model_dump(mode="json"),
            },
            output_payload_json=recommendation_payload,
            score_breakdown_json={
                **recommendation.ranking.score_breakdown,
                "final_score": recommendation.ranking.final_score,
                "decision": recommendation.ranking.decision,
            },
            risk_plan_json=recommendation.risk_plan.model_dump(mode="json"),
            news_risk_json=recommendation.news_risk.model_dump(mode="json"),
            regime_snapshot_json=recommendation.regime.model_dump(mode="json"),
            ai_review_json=recommendation.ai_analysis.model_dump(mode="json"),
            risk_review_json=recommendation.risk_review.model_dump(mode="json"),
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        log.info(
            "audit_recorded",
            extra={
                "audit_id": row.id,
                "instrument": recommendation.instrument,
                "decision": row.final_decision,
                "data_status": recommendation.data_status,
            },
        )
        return row.id
