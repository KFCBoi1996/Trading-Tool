from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint_returns_real_db_status() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert body["checks"]["trade_execution"] == "not_present"
    assert body["checks"]["database"] == "ok"


def test_candles_endpoint_returns_mock_status() -> None:
    response = client.get("/api/candles/EUR_USD?timeframe=M15&limit=5")
    assert response.status_code == 200
    candles = response.json()
    assert len(candles) == 5
    assert all(c["data_status"] == "MOCK" for c in candles)
    assert all(c["is_mock"] is True for c in candles)


def test_candles_endpoint_rejects_unknown_instrument() -> None:
    response = client.get("/api/candles/XXX_YYY?timeframe=M15")
    assert response.status_code == 404
    body = response.json()
    assert body["error"]["code"] == "http_error"
    assert "request_id" in body["error"]


def test_candles_endpoint_rejects_unknown_timeframe() -> None:
    response = client.get("/api/candles/EUR_USD?timeframe=ZZZ")
    assert response.status_code == 400
    body = response.json()
    assert body["error"]["code"] == "http_error"


def test_recommendation_fails_closed_on_mock_data() -> None:
    with client:
        response = client.get("/api/recommendations/EUR_USD")
    assert response.status_code == 200
    body = response.json()
    assert body["data_status"] == "MOCK"
    assert body["final_arbiter"]["display_mode"] != "trade_recommendation"
    assert body["final_arbiter"]["audit_required"] is True


def test_recommendation_round_trip_through_cache() -> None:
    with client:
        first = client.get("/api/recommendations/EUR_USD")
        second = client.get("/api/recommendations/EUR_USD")
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["instrument"] == second.json()["instrument"]
    assert second.json()["audit_id"]


def test_journal_endpoint_returns_audit_rows() -> None:
    with client:
        client.get("/api/recommendations/EUR_USD")
        response = client.get("/api/journal?limit=10")
    assert response.status_code == 200
    rows = response.json()
    assert isinstance(rows, list)
    assert len(rows) >= 1
    assert rows[0]["final_decision"]


def test_feature_flag_patch() -> None:
    with client:
        existing = client.get("/api/feature-flags").json()
        flag_name = existing[0]["flag_name"]
        response = client.patch(f"/api/feature-flags/{flag_name}", json={"enabled": False})
    assert response.status_code == 200
    body = response.json()
    assert body["flag_name"] == flag_name
    assert body["enabled"] is False


def test_outcome_tracker_endpoint_runs() -> None:
    with client:
        client.get("/api/recommendations/EUR_USD")
        response = client.post("/api/journal/outcome/track")
    assert response.status_code == 200
    body = response.json()
    assert "checked" in body
    assert "updated" in body


def test_validation_error_returns_envelope() -> None:
    with client:
        response = client.post("/api/journal/outcome/update", json={"outcome": "not_a_real_outcome"})
    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "validation_error"
    assert "request_id" in body["error"]
