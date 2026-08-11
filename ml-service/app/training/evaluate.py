"""Evaluation harness.

Computes, per label field (category / subcategory / urgency / sentiment):
  - accuracy
  - weighted F1
  - per-label (per-class) F1
  - confusion matrix

Plus overall:
  - prediction latency (mean / p50 / p95 / max, ms)
  - confidence distribution (mean / min / max / histogram bucket counts)

Used both as a standalone CLI/report generator and inside the retraining
pipeline to decide whether a candidate model is allowed to be promoted.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score

from app.labels import LABEL_FIELDS, LABEL_SPACE
from app.training.dataset import load_dataset, split_dataset


def _confidence_histogram(confidences: list[float], n_bins: int = 5) -> dict[str, int]:
    bins = np.linspace(0.0, 1.0, n_bins + 1)
    counts, _ = np.histogram(confidences, bins=bins)
    return {
        f"{bins[i]:.1f}-{bins[i+1]:.1f}": int(counts[i]) for i in range(n_bins)
    }


def evaluate_predictions(
    y_true: dict[str, list[str]],
    y_pred: dict[str, list[str]],
    confidences: dict[str, list[float]],
    latencies_ms: list[float],
) -> dict[str, Any]:
    """Pure metric computation over already-generated predictions.
    Kept separate from model loading so it's trivially unit-testable."""
    report: dict[str, Any] = {"per_field": {}, "overall": {}}

    for field in LABEL_FIELDS:
        labels = LABEL_SPACE[field]
        true_vals = y_true[field]
        pred_vals = y_pred[field]

        acc = accuracy_score(true_vals, pred_vals)
        weighted_f1 = f1_score(true_vals, pred_vals, average="weighted", labels=labels, zero_division=0)
        per_label_f1 = f1_score(true_vals, pred_vals, average=None, labels=labels, zero_division=0)
        cm = confusion_matrix(true_vals, pred_vals, labels=labels)

        report["per_field"][field] = {
            "accuracy": round(float(acc), 4),
            "weighted_f1": round(float(weighted_f1), 4),
            "per_label_f1": {label: round(float(f1), 4) for label, f1 in zip(labels, per_label_f1)},
            "confusion_matrix": {
                "labels": labels,
                "matrix": cm.tolist(),
            },
            "confidence": {
                "mean": round(float(np.mean(confidences[field])), 4) if confidences[field] else None,
                "min": round(float(np.min(confidences[field])), 4) if confidences[field] else None,
                "max": round(float(np.max(confidences[field])), 4) if confidences[field] else None,
                "histogram": _confidence_histogram(confidences[field]) if confidences[field] else {},
            },
        }

    # Overall summary uses category weighted F1 as the primary headline
    # metric (used for regression comparisons), plus latency stats.
    report["overall"] = {
        "primary_metric": "category_weighted_f1",
        "category_weighted_f1": report["per_field"]["category"]["weighted_f1"],
        "mean_weighted_f1_all_fields": round(
            float(np.mean([report["per_field"][f]["weighted_f1"] for f in LABEL_FIELDS])), 4
        ),
        "latency_ms": {
            "mean": round(float(np.mean(latencies_ms)), 3) if latencies_ms else None,
            "p50": round(float(np.percentile(latencies_ms, 50)), 3) if latencies_ms else None,
            "p95": round(float(np.percentile(latencies_ms, 95)), 3) if latencies_ms else None,
            "max": round(float(np.max(latencies_ms)), 3) if latencies_ms else None,
        },
        "n_examples": len(y_true["category"]),
    }
    return report


def evaluate_model(predictor, test_df: pd.DataFrame) -> dict[str, Any]:
    """Run a loaded predictor (anything exposing `.predict(text) -> dict[field, (label, confidence)]`)
    over a labeled test set and produce a full evaluation report."""
    y_true: dict[str, list[str]] = {field: [] for field in LABEL_FIELDS}
    y_pred: dict[str, list[str]] = {field: [] for field in LABEL_FIELDS}
    confidences: dict[str, list[float]] = {field: [] for field in LABEL_FIELDS}
    latencies_ms: list[float] = []

    for _, row in test_df.iterrows():
        start = time.perf_counter()
        prediction = predictor.predict(row["text"])
        latencies_ms.append((time.perf_counter() - start) * 1000)

        for field in LABEL_FIELDS:
            label, confidence = prediction[field]
            y_true[field].append(row[field])
            y_pred[field].append(label)
            confidences[field].append(confidence)

    return evaluate_predictions(y_true, y_pred, confidences, latencies_ms)


def evaluate_artifact(artifact_dir: Path, model_type: str, dataset_path: Path | None = None) -> dict:
    """CLI-friendly helper: load an artifact by path/type and evaluate it
    against the held-out split of a dataset."""
    from app.training.sklearn_baseline import SklearnBaselinePredictor
    from app.inference.transformer_predictor import TransformerPredictorAdapter

    df = load_dataset(dataset_path)
    split = split_dataset(df)

    if model_type == "sklearn_baseline":
        predictor = SklearnBaselinePredictor(artifact_dir)
    elif model_type == "transformer":
        predictor = TransformerPredictorAdapter(artifact_dir)
    else:
        raise ValueError(f"Unknown model_type: {model_type}")

    return evaluate_model(predictor, split.test)


def _cli() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Evaluate a trained TriageFlow model.")
    parser.add_argument("--artifact-dir", required=True)
    parser.add_argument("--model-type", choices=["sklearn_baseline", "transformer"], required=True)
    parser.add_argument("--dataset", default=None)
    parser.add_argument("--out", default=None, help="Optional path to write the JSON report to.")
    args = parser.parse_args()

    report = evaluate_artifact(
        Path(args.artifact_dir), args.model_type, Path(args.dataset) if args.dataset else None
    )
    text = json.dumps(report, indent=2)
    print(text)
    if args.out:
        Path(args.out).write_text(text)


if __name__ == "__main__":
    _cli()
