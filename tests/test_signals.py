from fastapi.testclient import TestClient

from trading_tool.api.app import app


client = TestClient(app)


def test_generate_signal() -> None:
    response = client.post("/v1/signals", json={"symbol": "AAPL", "timeframe": "1D"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["symbol"] == "AAPL"
    assert payload["action"] in {"BUY", "HOLD", "SELL"}
