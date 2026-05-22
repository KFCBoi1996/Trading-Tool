from pydantic import BaseModel, Field


class SignalRequest(BaseModel):
    symbol: str = Field(min_length=1, examples=["AAPL"])
    timeframe: str = Field(default="1D", examples=["1D", "1H"])


class SignalResponse(BaseModel):
    symbol: str
    timeframe: str
    score: float
    action: str
