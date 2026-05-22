from trading_tool.core.models import SignalRequest, SignalResponse


class SignalEngine:
    """Simple deterministic signal engine placeholder."""

    def generate(self, request: SignalRequest) -> SignalResponse:
        seed = sum(ord(char) for char in request.symbol.upper()) % 100
        score = round(seed / 100, 2)
        action = "BUY" if score >= 0.6 else "HOLD" if score >= 0.4 else "SELL"
        return SignalResponse(
            symbol=request.symbol.upper(),
            timeframe=request.timeframe,
            score=score,
            action=action,
        )
