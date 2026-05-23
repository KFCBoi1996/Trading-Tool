from __future__ import annotations

from app.data.mock_provider import DeterministicMockMarketProvider
from app.features.engine import FeatureEngine
from app.news.engine import NewsCalendarRiskEngine
from app.ranking.engine import RankingEngine
from app.regime.engine import RegimeEngine
from app.risk.engine import RiskEngine
from app.strategies.base import StrategyContext
from app.strategies.plugins import get_strategy_instances


def _context() -> StrategyContext:
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


def test_all_strategies_return_schema_and_evidence() -> None:
    context = _context()
    strategies = get_strategy_instances()
    assert len(strategies) == 12
    seen_ids: set[str] = set()
    for strategy in strategies:
        signal = strategy.evaluate(context)
        assert signal.strategy_id == strategy.strategy_id
        assert signal.strategy_version == "1.0.0"
        assert signal.evidence, "strategies must include evidence ids"
        assert signal.status in {"active", "watchlist", "rejected"}
        assert signal.direction in {"long", "short", "none"}
        assert 0 <= signal.raw_confidence <= 100
        assert signal.data_status in {"LIVE", "DELAYED", "MOCK", "STALE", "DEGRADED", "UNAVAILABLE"}
        seen_ids.add(signal.strategy_id)
    assert len(seen_ids) == 12


def test_risk_engine_rejects_missing_stop_loss() -> None:
    context = _context()
    signal = get_strategy_instances()[0].evaluate(context)
    mutated = signal.model_copy(update={"suggested_stop": None})
    plan = RiskEngine().build_plan(mutated, context.setup_features, context.quote, context.news_risk)
    assert plan.rejection_reason == "Missing stop loss"


def test_risk_engine_rejects_missing_take_profit() -> None:
    context = _context()
    signal = get_strategy_instances()[0].evaluate(context)
    mutated = signal.model_copy(
        update={
            "direction": "long",
            "entry_zone": {"low": 1.1000, "high": 1.1010},
            "suggested_stop": 1.0980,
            "suggested_targets": [None, None],
        }
    )
    plan = RiskEngine().build_plan(mutated, context.setup_features, context.quote, context.news_risk)
    assert plan.rejection_reason == "Missing take profit"


def test_ranking_blocks_when_data_quality_fails() -> None:
    context = _context()
    signal = get_strategy_instances()[0].evaluate(context)
    plan = RiskEngine().build_plan(signal, context.setup_features, context.quote, context.news_risk)
    ranking = RankingEngine().rank(signal, context.regime, context.news_risk, plan, data_quality_passed=False)
    assert ranking.decision == "no_trade"
    assert ranking.rejection_reason
