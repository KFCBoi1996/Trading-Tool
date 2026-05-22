from __future__ import annotations

from datetime import timedelta
from app.constants import MINIMUM_REWARD_RISK, PAIR_SPREAD_LIMIT_PIPS, RISK_ENGINE_VERSION
from app.schemas import FeatureSnapshot, NewsRiskOut, QuoteOut, RiskPlanOut, StrategySignalOut

class RiskEngine:
    def build_plan(self, signal: StrategySignalOut, features: FeatureSnapshot, quote: QuoteOut, news_risk: NewsRiskOut) -> RiskPlanOut:
        entry_low = signal.entry_zone.get("low")
        entry_high = signal.entry_zone.get("high")
        stop = signal.suggested_stop
        tp1 = signal.suggested_targets[0] if signal.suggested_targets else None
        tp2 = signal.suggested_targets[1] if len(signal.suggested_targets) > 1 else None
        rejection = None
        rr1 = rr2 = None
        if stop is None:
            rejection = "Missing stop loss"
        elif tp1 is None:
            rejection = "Missing take profit"
        elif entry_low is None or entry_high is None:
            rejection = "Missing entry zone"
        else:
            if signal.direction == "long":
                entry = entry_high
                risk = entry - stop
                reward1 = tp1 - entry
                reward2 = (tp2 - entry) if tp2 is not None else None
                missed = quote.mid > entry_high + (features.atr14 or 0) * 1.5
            elif signal.direction == "short":
                entry = entry_low
                risk = stop - entry
                reward1 = entry - tp1
                reward2 = (entry - tp2) if tp2 is not None else None
                missed = quote.mid < entry_low - (features.atr14 or 0) * 1.5
            else:
                risk = reward1 = 0.0
                reward2 = None
                missed = False
            if risk <= 0:
                rejection = "Stop distance is invalid"
            else:
                rr1 = reward1 / risk
                rr2 = reward2 / risk if reward2 is not None else None
                if rr1 < MINIMUM_REWARD_RISK:
                    rejection = "Reward/risk is below 1.5"
                elif quote.spread_pips > PAIR_SPREAD_LIMIT_PIPS[signal.instrument]:
                    rejection = "Spread is too wide"
                elif missed:
                    rejection = "Entry is already missed"
                elif news_risk.blackout_active:
                    rejection = "High-impact news blackout is active"
        valid_until = (features.timestamp + timedelta(minutes=45)) if features.timestamp and signal.trigger_timeframe == "M15" else (features.timestamp + timedelta(hours=3)) if features.timestamp else None
        return RiskPlanOut(
            risk_engine_version=RISK_ENGINE_VERSION,
            entry_type="limit_retest" if signal.status == "active" else "watchlist_trigger" if signal.status == "watchlist" else "none",
            entry_low=entry_low,
            entry_high=entry_high,
            stop_loss=stop,
            tp1=tp1,
            tp2=tp2,
            rr_to_tp1=round(rr1, 2) if rr1 is not None else None,
            rr_to_tp2=round(rr2, 2) if rr2 is not None else None,
            invalidation="Setup invalidates if price closes beyond the stop structure or the entry window expires.",
            stop_reason="Stop is placed beyond recent swing structure plus ATR/spread buffer." if stop is not None else "No stop generated.",
            tp_reason="Targets are derived from reward/risk and nearby deterministic structure." if tp1 is not None else "No take-profit generated.",
            entry_valid_until=valid_until,
            valid_for_candles=3,
            missed_entry=bool(rejection == "Entry is already missed"),
            cost_in_r=round((quote.spread_pips / 10), 3),
            rejection_reason=rejection,
        )
