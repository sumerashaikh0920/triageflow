"""Tests for evaluate.py's pure metric computation (accuracy, weighted F1,
per-label F1, confusion matrix, latency, confidence distribution)."""
from __future__ import annotations

from app.labels import LABEL_FIELDS, LABEL_SPACE
from app.training.evaluate import evaluate_predictions


def _perfect_predictions():
    y_true = {
        "category": ["billing", "technical", "billing", "account"],
        "subcategory": ["billing_refund", "technical_bug", "billing_refund", "account_login"],
        "urgency": ["high", "low", "high", "medium"],
        "sentiment": ["negative", "neutral", "negative", "neutral"],
    }
    y_pred = {k: list(v) for k, v in y_true.items()}
    confidences = {field: [0.9, 0.85, 0.95, 0.8] for field in LABEL_FIELDS}
    latencies = [10.0, 12.0, 9.5, 11.0]
    return y_true, y_pred, confidences, latencies


def test_perfect_predictions_yield_accuracy_one():
    y_true, y_pred, confidences, latencies = _perfect_predictions()
    report = evaluate_predictions(y_true, y_pred, confidences, latencies)

    for field in LABEL_FIELDS:
        assert report["per_field"][field]["accuracy"] == 1.0
        assert report["per_field"][field]["weighted_f1"] == 1.0

    assert report["overall"]["category_weighted_f1"] == 1.0
    assert report["overall"]["n_examples"] == 4


def test_report_contains_confusion_matrix_with_correct_shape():
    y_true, y_pred, confidences, latencies = _perfect_predictions()
    report = evaluate_predictions(y_true, y_pred, confidences, latencies)

    cm = report["per_field"]["category"]["confusion_matrix"]
    n_labels = len(LABEL_SPACE["category"])
    assert len(cm["labels"]) == n_labels
    assert len(cm["matrix"]) == n_labels
    assert all(len(row) == n_labels for row in cm["matrix"])


def test_report_contains_per_label_f1_for_every_label():
    y_true, y_pred, confidences, latencies = _perfect_predictions()
    report = evaluate_predictions(y_true, y_pred, confidences, latencies)

    for field in LABEL_FIELDS:
        per_label_f1 = report["per_field"][field]["per_label_f1"]
        assert set(per_label_f1.keys()) == set(LABEL_SPACE[field])


def test_wrong_predictions_lower_accuracy():
    y_true, y_pred, confidences, latencies = _perfect_predictions()
    # Corrupt every category prediction.
    y_pred["category"] = ["technical", "billing", "account", "billing"]

    report = evaluate_predictions(y_true, y_pred, confidences, latencies)
    assert report["per_field"]["category"]["accuracy"] == 0.0
    assert report["overall"]["category_weighted_f1"] == 0.0


def test_latency_and_confidence_stats_computed():
    y_true, y_pred, confidences, latencies = _perfect_predictions()
    report = evaluate_predictions(y_true, y_pred, confidences, latencies)

    latency_stats = report["overall"]["latency_ms"]
    assert latency_stats["mean"] > 0
    assert latency_stats["p50"] > 0
    assert latency_stats["p95"] >= latency_stats["p50"]

    conf_stats = report["per_field"]["category"]["confidence"]
    assert conf_stats["mean"] is not None
    assert conf_stats["min"] <= conf_stats["mean"] <= conf_stats["max"]
    assert sum(conf_stats["histogram"].values()) == 4
