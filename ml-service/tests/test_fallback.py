"""Tests for the pure heuristic fallback classifier and the predictor's
graceful fallback when no model can be loaded."""
from __future__ import annotations

from app.labels import CATEGORIES, SENTIMENTS, SUBCATEGORY_TO_CATEGORY, URGENCY_LEVELS


def test_heuristic_returns_valid_labels():
    from app.inference.heuristic import classify

    result = classify(
        "Production is down",
        "Our production system is completely down right now, this is urgent, please help immediately.",
    )
    assert result.category in CATEGORIES
    assert result.urgency in URGENCY_LEVELS
    assert result.sentiment in SENTIMENTS
    assert SUBCATEGORY_TO_CATEGORY[result.subcategory] == result.category
    for v in result.confidence.values():
        assert 0.0 <= v <= 1.0


def test_heuristic_detects_billing_keywords():
    from app.inference.heuristic import classify

    result = classify("Refund request", "I need a refund for my last invoice charge.")
    assert result.category == "billing"


def test_heuristic_detects_urgency_language():
    from app.inference.heuristic import classify

    urgent = classify("URGENT", "This is urgent, please fix immediately, production down right now.")
    calm = classify("Small question", "Just a small question about my account, no rush.")
    urgency_rank = {u: i for i, u in enumerate(URGENCY_LEVELS)}
    assert urgency_rank[urgent.urgency] >= urgency_rank[calm.urgency]


def test_heuristic_sentiment_detection():
    from app.inference.heuristic import classify

    negative = classify("Angry", "This is unacceptable and I am extremely frustrated with this broken product.")
    positive = classify("Thanks", "Thank you so much, I really appreciate the great support, awesome job.")
    assert negative.sentiment == "negative"
    assert positive.sentiment == "positive"


def test_predictor_falls_back_when_no_active_model(tmp_env, db_session):
    """With a fresh, empty registry (no bootstrap run), the predictor
    service must still return a structurally valid heuristic prediction
    rather than erroring."""
    from app.inference.predictor import PredictorService

    service = PredictorService()
    result = service.predict("Help", "My account is locked and I cannot log in, please help urgently.")

    assert result["model_type"] == "heuristic_fallback"
    assert result["model_version"] == "heuristic-fallback-v1"
    assert result["category"] in CATEGORIES
    assert "fallback" in result["reason"].lower() or "heuristic" in result["reason"].lower()
