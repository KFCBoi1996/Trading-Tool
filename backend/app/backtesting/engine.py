from __future__ import annotations

from app.schemas import BacktestSummaryOut


class BacktestingEngine:
    def summarize(self, strategy_id: str, strategy_version: str, instrument: str, timeframe: str) -> BacktestSummaryOut:
        return BacktestSummaryOut(
            strategy_id=strategy_id,
            strategy_version=strategy_version,
            instrument=instrument,
            timeframe=timeframe,
            sample_size=0,
            win_rate=None,
            average_r=None,
            expected_r=None,
            profit_factor=None,
            max_drawdown_r=None,
            average_adverse_excursion_r=None,
            average_favorable_excursion_r=None,
            average_time_in_trade_minutes=None,
            confidence_penalty=15.0,
            status="Backtest unavailable: no stored historical sample has been calculated.",
        )
