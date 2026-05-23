from __future__ import annotations

from statistics import mean

from app.constants import PAIR_SPREAD_LIMIT_PIPS
from app.schemas import CandleOut, FeatureSnapshot, QuoteOut


def _sma(values: list[float], period: int) -> float | None:
    return mean(values[-period:]) if len(values) >= period else None

def _ema(values: list[float], period: int) -> float | None:
    if len(values) < period:
        return None
    k = 2 / (period + 1)
    ema = mean(values[:period])
    for value in values[period:]:
        ema = value * k + ema * (1 - k)
    return ema

def _rsi(values: list[float], period: int = 14) -> float | None:
    if len(values) <= period:
        return None
    gains: list[float] = []
    losses: list[float] = []
    for previous, current in zip(values[-period - 1:-1], values[-period:], strict=False):
        delta = current - previous
        gains.append(max(delta, 0))
        losses.append(abs(min(delta, 0)))
    avg_gain = mean(gains)
    avg_loss = mean(losses)
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def _atr(candles: list[CandleOut], period: int = 14) -> float | None:
    if len(candles) <= period:
        return None
    true_ranges: list[float] = []
    for previous, candle in zip(candles[-period - 1:-1], candles[-period:], strict=False):
        true_ranges.append(max(candle.high - candle.low, abs(candle.high - previous.close), abs(candle.low - previous.close)))
    return mean(true_ranges)

def _macd(values: list[float]) -> dict[str, float | None]:
    ema12 = _ema(values, 12)
    ema26 = _ema(values, 26)
    if ema12 is None or ema26 is None:
        return {"line": None, "signal": None, "histogram": None}
    line = ema12 - ema26
    recent_lines = []
    for idx in range(26, len(values) + 1):
        e12 = _ema(values[:idx], 12)
        e26 = _ema(values[:idx], 26)
        if e12 is not None and e26 is not None:
            recent_lines.append(e12 - e26)
    signal = _ema(recent_lines, 9) if len(recent_lines) >= 9 else None
    histogram = line - signal if signal is not None else None
    return {"line": line, "signal": signal, "histogram": histogram}

def _adx(candles: list[CandleOut], period: int = 14) -> float | None:
    if len(candles) <= period + 1:
        return None
    directional_moves = []
    ranges = []
    for previous, candle in zip(candles[-period - 1:-1], candles[-period:], strict=False):
        directional_moves.append(abs(candle.high - previous.high) + abs(candle.low - previous.low))
        ranges.append(max(candle.high - candle.low, abs(candle.high - previous.close), abs(candle.low - previous.close)))
    if not ranges or mean(ranges) == 0:
        return 0.0
    return min(100.0, (mean(directional_moves) / mean(ranges)) * 50)

def _swings(candles: list[CandleOut]) -> tuple[list[float], list[float]]:
    highs: list[float] = []
    lows: list[float] = []
    for idx in range(2, len(candles) - 2):
        window = candles[idx - 2:idx + 3]
        if candles[idx].high == max(c.high for c in window):
            highs.append(candles[idx].high)
        if candles[idx].low == min(c.low for c in window):
            lows.append(candles[idx].low)
    return highs[-5:], lows[-5:]

class FeatureEngine:
    def calculate(self, instrument: str, timeframe: str, candles: list[CandleOut], quote: QuoteOut | None) -> FeatureSnapshot:
        latest = candles[-1] if candles else None
        closes = [c.close for c in candles]
        highs = [c.high for c in candles]
        lows = [c.low for c in candles]
        ema20 = _ema(closes, 20)
        ema50 = _ema(closes, 50)
        ema200 = _ema(closes, 200)
        sma50 = _sma(closes, 50)
        sma200 = _sma(closes, 200)
        rsi14 = _rsi(closes)
        atr14 = _atr(candles)
        adx14 = _adx(candles)
        bb_mid = _sma(closes, 20)
        bb_width = atr14 * 2 if atr14 is not None else None
        bollinger = {"upper": bb_mid + bb_width if bb_mid is not None and bb_width is not None else None, "middle": bb_mid, "lower": bb_mid - bb_width if bb_mid is not None and bb_width is not None else None}
        donchian = {"high": max(highs[-20:]) if len(highs) >= 20 else None, "low": min(lows[-20:]) if len(lows) >= 20 else None}
        swing_highs, swing_lows = _swings(candles)
        support = sorted(swing_lows[-3:])
        resistance = sorted(swing_highs[-3:])
        latest_close = latest.close if latest else None
        distance_to_support = min((abs(latest_close - s) for s in support), default=None) if latest_close is not None else None
        distance_to_resistance = min((abs(r - latest_close) for r in resistance), default=None) if latest_close is not None else None
        trend_direction = "neutral"
        if latest_close is not None and ema50 is not None and ema200 is not None:
            if latest_close > ema50 > ema200:
                trend_direction = "bullish"
            elif latest_close < ema50 < ema200:
                trend_direction = "bearish"
        trend_strength = min(100.0, adx14 or 0.0)
        range_strength = 100.0 - min(100.0, trend_strength)
        atr_percentage = (atr14 / latest_close) * 100 if atr14 is not None and latest_close else None
        avg_range = mean([c.high - c.low for c in candles[-20:]]) if len(candles) >= 20 else None
        latest_range = (latest.high - latest.low) if latest else None
        candle_range_relative_to_atr = (latest_range / atr14) if latest_range is not None and atr14 else None
        volatility_compression = bool(avg_range and atr14 and atr14 < avg_range * 0.75)
        volatility_expansion = bool(avg_range and atr14 and atr14 > avg_range * 1.25)
        volatility_state = "compressed" if volatility_compression else "expanding" if volatility_expansion else "normal"
        hour = latest.timestamp.hour if latest else 0
        session_state = "asia" if 0 <= hour < 7 else "london" if 7 <= hour < 12 else "overlap" if 12 <= hour < 16 else "new_york" if 16 <= hour < 21 else "low_liquidity"
        spread_passed = quote.spread_pips <= PAIR_SPREAD_LIMIT_PIPS[instrument] if quote else False
        breakout_status = "breakout_watch" if donchian["high"] and latest_close and latest_close > donchian["high"] * 0.999 else "none"
        pullback_status = "ema_pullback" if latest_close and ema20 and abs(latest_close - ema20) <= (atr14 or 0) else "none"
        liquidity_sweep_status = "possible_sweep" if swing_highs and swing_lows and latest and (latest.high > max(swing_highs) or latest.low < min(swing_lows)) else "none"
        previous_day = candles[-96:] if timeframe == "M15" and len(candles) >= 96 else candles[-24:] if timeframe == "H1" and len(candles) >= 24 else []
        previous_week = candles[-480:] if timeframe == "M15" and len(candles) >= 480 else []
        return FeatureSnapshot(
            instrument=instrument,
            timeframe=timeframe,
            timestamp=latest.timestamp if latest else None,
            ema20=ema20, ema50=ema50, ema200=ema200, sma50=sma50, sma200=sma200, rsi14=rsi14,
            macd=_macd(closes), atr14=atr14, adx14=adx14, bollinger=bollinger, donchian=donchian,
            recent_swing_highs=swing_highs, recent_swing_lows=swing_lows, support_zones=support, resistance_zones=resistance,
            previous_day_high=max([c.high for c in previous_day], default=None), previous_day_low=min([c.low for c in previous_day], default=None),
            previous_week_high=max([c.high for c in previous_week], default=None), previous_week_low=min([c.low for c in previous_week], default=None),
            distance_to_support=distance_to_support, distance_to_resistance=distance_to_resistance,
            asian_session_range={"high": max([c.high for c in candles[-32:]], default=None), "low": min([c.low for c in candles[-32:]], default=None)},
            london_session_state="active" if session_state in {"london", "overlap"} else "inactive",
            new_york_session_state="active" if session_state in {"new_york", "overlap"} else "inactive",
            london_new_york_overlap=session_state == "overlap", low_liquidity_period=session_state == "low_liquidity",
            atr_percentage=atr_percentage, volatility_compression=volatility_compression, volatility_expansion=volatility_expansion,
            candle_range_relative_to_atr=candle_range_relative_to_atr, current_spread_pips=quote.spread_pips if quote else None,
            spread_threshold_passed=spread_passed, spread_cost_in_r=None, trend_direction=trend_direction, trend_strength=trend_strength,
            range_strength=range_strength, volatility_state=volatility_state, session_state=session_state, higher_timeframe_bias=trend_direction,
            breakout_status=breakout_status, pullback_status=pullback_status, liquidity_sweep_status=liquidity_sweep_status,
            data_status=latest.data_status if latest else "UNAVAILABLE", is_mock=latest.is_mock if latest else False,
        )
