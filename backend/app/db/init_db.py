from __future__ import annotations

from sqlalchemy.orm import Session

from app.constants import FEATURE_FLAGS, SUPPORTED_INSTRUMENTS
from app.strategies.plugins import get_strategy_instances

from .models import FeatureFlag, Instrument, StrategyDefinition
from .session import Base, engine

FLAG_DESCRIPTIONS = {
    "AI_ANALYST_ENABLED": "Allow structured AI analyst summaries when an LLM key is configured.",
    "AI_RISK_REVIEWER_ENABLED": "Allow structured AI risk review when an LLM key is configured.",
    "MOCK_DATA_ENABLED": "Enable deterministic MOCK_DATA providers.",
    "LIVE_PROVIDER_ENABLED": "Enable live provider adapters when keys are configured.",
    "LIVE_RECOMMENDATIONS_ENABLED": "Allow user-facing live recommendations after all safety gates pass.",
    "BACKTEST_SCORING_ENABLED": "Use calculated backtest summaries in ranking.",
    "NEWS_SCORING_ENABLED": "Use news/calendar risk in ranking.",
    "ALERTS_ENABLED": "Enable in-app alert creation after arbiter approval.",
    "PAPER_VALIDATION_MODE_ENABLED": "Journal outputs without showing user-facing trade recommendations.",
    "CHALLENGER_STRATEGIES_ENABLED": "Run challenger strategies in paper validation mode.",
}

def create_db_and_tables() -> None:
    Base.metadata.create_all(bind=engine)

def seed_reference_data(db: Session) -> None:
    for symbol, meta in SUPPORTED_INSTRUMENTS.items():
        existing = db.query(Instrument).filter(Instrument.symbol == symbol).first()
        if existing is None:
            db.add(Instrument(symbol=symbol, base_currency=meta["base"], quote_currency=meta["quote"], pip_size=meta["pip_size"], price_precision=meta["precision"], is_active=True))
    for flag, enabled in FEATURE_FLAGS.items():
        existing = db.query(FeatureFlag).filter(FeatureFlag.flag_name == flag).first()
        if existing is None:
            db.add(FeatureFlag(flag_name=flag, enabled=enabled, description=FLAG_DESCRIPTIONS.get(flag, flag)))
    for strategy in get_strategy_instances():
        existing = db.query(StrategyDefinition).filter(StrategyDefinition.strategy_id == strategy.strategy_id, StrategyDefinition.strategy_version == strategy.strategy_version).first()
        if existing is None:
            db.add(StrategyDefinition(strategy_id=strategy.strategy_id, strategy_version=strategy.strategy_version, name=strategy.description, family=strategy.family, description=strategy.description, is_active=True, parameters_json=strategy.parameters))
    db.commit()
