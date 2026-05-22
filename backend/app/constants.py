from __future__ import annotations

SUPPORTED_INSTRUMENTS = {
    "EUR_USD": {"display": "EUR/USD", "base": "EUR", "quote": "USD", "pip_size": 0.0001, "precision": 5},
    "GBP_USD": {"display": "GBP/USD", "base": "GBP", "quote": "USD", "pip_size": 0.0001, "precision": 5},
    "USD_JPY": {"display": "USD/JPY", "base": "USD", "quote": "JPY", "pip_size": 0.01, "precision": 3},
    "AUD_USD": {"display": "AUD/USD", "base": "AUD", "quote": "USD", "pip_size": 0.0001, "precision": 5},
    "USD_CAD": {"display": "USD/CAD", "base": "USD", "quote": "CAD", "pip_size": 0.0001, "precision": 5},
}
SUPPORTED_TIMEFRAMES = ("M15", "H1", "H4")
DATA_STATUSES = ("LIVE", "DELAYED", "MOCK", "STALE", "DEGRADED", "UNAVAILABLE")
BLOCKING_DATA_STATUSES = {"MOCK", "STALE", "DEGRADED", "UNAVAILABLE"}
RECOMMENDATION_THRESHOLD = 75.0
WATCHLIST_THRESHOLD = 65.0
MINIMUM_REWARD_RISK = 1.5
RANKING_VERSION = "ranking_rules_v1.0.0"
RISK_ENGINE_VERSION = "risk_engine_v1.0.0"
ARBITER_VERSION = "arbiter_rules_v1.0.0"
ANALYST_PROMPT_VERSION = "analyst_prompt_v1.0.0"
RISK_REVIEWER_PROMPT_VERSION = "risk_reviewer_prompt_v1.0.0"
FEATURE_FLAGS = {
    "AI_ANALYST_ENABLED": True,
    "AI_RISK_REVIEWER_ENABLED": True,
    "MOCK_DATA_ENABLED": True,
    "LIVE_PROVIDER_ENABLED": False,
    "LIVE_RECOMMENDATIONS_ENABLED": False,
    "BACKTEST_SCORING_ENABLED": False,
    "NEWS_SCORING_ENABLED": True,
    "ALERTS_ENABLED": True,
    "PAPER_VALIDATION_MODE_ENABLED": True,
    "CHALLENGER_STRATEGIES_ENABLED": False,
}
PAIR_SPREAD_LIMIT_PIPS = {
    "EUR_USD": 2.0,
    "GBP_USD": 2.5,
    "USD_JPY": 2.5,
    "AUD_USD": 2.5,
    "USD_CAD": 2.8,
}
