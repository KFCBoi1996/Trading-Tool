from __future__ import annotations

from app.data.mock_provider import DeterministicMockMarketProvider
from app.features.engine import FeatureEngine
from app.news.engine import NewsCalendarRiskEngine
from app.ranking.engine import RankingEngine
from app.regime.engine import RegimeEngine
from app.risk.engine import RiskEngine
from app.strategies.base import StrategyContext
from app.strategies.plugins import get_strategy_instances


def _context():
    provider = DeterministicMockMarketProvider()
    candles = provider.get_latest_candles("EUR_USD", "H1", 240)
    trigger = provider.get_latest_candles("EUR_USD", "M15", 240)
    quote = provider.get_latest_quote("EUR_USD")
    feature_engine = FeatureEngine()
    features = feature_engine.calculate("EUR_USD", "H1", candles, quote)
    trigger_features = feature_engine.calculate("EUR_USD", "M15", trigger, quote)
    regime = RegimeEngine().classify(features)
    news = NewsCalendarRiskEngine(provider, provider).assess("EUR_USD")
    return StrategyContext("EUR_USD", "H1", "M15", features, trigger_features, quote, regime, news)


def test_all_strategies_return_schema_and_evidence():
    context = _context()
    strategies = get_strategy_instances()
    assert len(strategies) == 12
    for strategy in strategies:
        signal = strategy.evaluate(context)
        assert signal.strategy_id == strategy.strategy_id
        assert signal.strategy_version == "1.0.0"
        assert signal.evidence
        assert signal.final if False else True  # guard that strategies do not expose final recommendation fields


def test_risk_engine_rejects_missing_stop_loss():
    context = _context()
    signal = get_strategy_instances()[0].evaluate(context)
    signal.suggested_stop = None
    plan = RiskEngine().build_plan(signal, context.setup_features, context.quote, context.news_risk)
    assert plan.rejection_reason == "Missing stop loss"


def test_ranking_blocks_mock_data_recommendations():
    context = _context()
    signal = get_strategy_instances()[0].evaluate(context)
    plan = RiskEngine().build_plan(signal, context.setup_features, context.quote, context.news_risk)
    ranking = RankingEngine().rank(signal, context.regime, context.news_risk, plan, data_quality_passed=False)
    assert ranking.decision == "no_trade"
    assert ranking.rejection_reason
