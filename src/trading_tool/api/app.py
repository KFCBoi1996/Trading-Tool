from fastapi import FastAPI

from trading_tool.config import config
from trading_tool.core.models import SignalRequest, SignalResponse
from trading_tool.services.signal_engine import SignalEngine

app = FastAPI(title=config.app_name, version=config.app_version)
engine = SignalEngine()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "environment": config.environment}


@app.post("/v1/signals", response_model=SignalResponse)
def generate_signal(payload: SignalRequest) -> SignalResponse:
    return engine.generate(payload)
