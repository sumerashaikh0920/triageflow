"""Tests for POST /predict response shape and GET /health."""
from __future__ import annotations


def test_predict_returns_expected_shape(client):
    resp = client.post(
        "/predict",
        json={
            "ticket_id": "T-TEST-1",
            "subject": "Cannot log in to my account",
            "body": "I keep getting an error when I try to log in, this is urgent, I need access today.",
        },
    )
    assert resp.status_code == 200
    data = resp.json()

    for field in [
        "category", "subcategory", "urgency", "sentiment",
        "confidence", "overall_confidence", "routing_team", "reason",
        "model_version", "model_type", "model_timestamp", "predicted_at", "latency_ms",
    ]:
        assert field in data, f"missing field: {field}"

    assert data["ticket_id"] == "T-TEST-1"
    assert isinstance(data["confidence"], dict)
    for label_field in ["category", "subcategory", "urgency", "sentiment"]:
        assert label_field in data["confidence"]
        assert 0.0 <= data["confidence"][label_field] <= 1.0

    assert 0.0 <= data["overall_confidence"] <= 1.0
    assert isinstance(data["routing_team"], str) and data["routing_team"]
    assert isinstance(data["reason"], str) and len(data["reason"]) > 0
    assert data["latency_ms"] >= 0


def test_predict_rejects_blank_body(client):
    resp = client.post("/predict", json={"subject": "Hi", "body": "   "})
    assert resp.status_code == 422


def test_health_endpoint(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ("ok", "degraded")
    assert data["service"] == "triageflow-ml"
    assert "database_ok" in data


def test_predict_category_is_valid_label(client):
    from app.labels import CATEGORIES, SENTIMENTS, URGENCY_LEVELS

    resp = client.post(
        "/predict",
        json={"subject": "Refund question", "body": "I was charged twice, please refund me."},
    )
    data = resp.json()
    assert data["category"] in CATEGORIES
    assert data["urgency"] in URGENCY_LEVELS
    assert data["sentiment"] in SENTIMENTS
