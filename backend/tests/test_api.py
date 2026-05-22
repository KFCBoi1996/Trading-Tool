from __future__ import annotations

import os
os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert body["checks"]["trade_execution"] == "not_present"


def test_candles_endpoint_returns_mock_status():
    response = client.get("/api/candles/EUR_USD?timeframe=M15&limit=5")
    assert response.status_code == 200
    candles = response.json()
    assert len(candles) == 5
    assert candles[0]["data_status"] == "MOCK"
    assert candles[0]["is_mock"] is True


def test_recommendation_fails_closed_on_mock_data():
    with client:
        response = client.get("/api/recommendations/EUR_USD")
    assert response.status_code == 200
    body = response.json()
    assert body["data_status"] == "MOCK"
    assert body["final_arbiter"]["display_mode"] != "trade_recommendation"
    assert body["final_arbiter"]["audit_required"] is True
