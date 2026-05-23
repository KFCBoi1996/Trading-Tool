from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.schemas import FeatureSnapshot, NewsRiskOut, QuoteOut, RegimeSnapshotOut, StrategySignalOut


@dataclass(frozen=True)
class StrategyContext:
    instrument: str
    setup_timeframe: str
    trigger_timeframe: str
    setup_features: FeatureSnapshot
    trigger_features: FeatureSnapshot
    quote: QuoteOut
    regime: RegimeSnapshotOut
    news_risk: NewsRiskOut

class BaseStrategy(ABC):
    strategy_id: str
    strategy_version = "1.0.0"
    family: str
    description: str
    parameters: dict

    @abstractmethod
    def evaluate(self, context: StrategyContext) -> StrategySignalOut:
        raise NotImplementedError
