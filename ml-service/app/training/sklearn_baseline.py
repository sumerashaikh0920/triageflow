"""Lightweight default model: one TF-IDF + LogisticRegression pipeline per
label field (category, subcategory, urgency, sentiment).

This is intentionally simple so the service is fully functional (real
predictions, real confidences) on a laptop with no GPU and no pretrained
transformer download — it's the "lightweight default model" referenced in
the spec, with the keyword heuristic in `heuristic.py` as the deeper
fallback if even this can't be loaded/trained.
"""
from __future__ import annotations

import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from app.labels import LABEL_FIELDS


def _build_pipeline() -> Pipeline:
    return Pipeline(
        [
            ("tfidf", TfidfVectorizer(
                ngram_range=(1, 2),
                min_df=1,
                max_features=20000,
                sublinear_tf=True,
            )),
            ("clf", LogisticRegression(
                max_iter=1000,
                class_weight="balanced",
                C=2.0,
            )),
        ]
    )


def train_sklearn_baseline(train_df: pd.DataFrame, output_dir: Path) -> dict:
    """Fit one pipeline per label field and persist them + label metadata."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for field in LABEL_FIELDS:
        pipeline = _build_pipeline()
        pipeline.fit(train_df["text"], train_df[field])
        joblib.dump(pipeline, output_dir / f"{field}_pipeline.joblib")

    meta = {
        "model_type": "sklearn_baseline",
        "n_training_examples": len(train_df),
        "fields": LABEL_FIELDS,
    }
    with open(output_dir / "artifact_meta.json", "w") as f:
        json.dump(meta, f, indent=2)
    return meta


class SklearnBaselinePredictor:
    """Loads persisted per-field pipelines and exposes a unified predict()."""

    def __init__(self, artifact_dir: Path) -> None:
        self.artifact_dir = Path(artifact_dir)
        self._pipelines: dict[str, Pipeline] = {}
        for field in LABEL_FIELDS:
            path = self.artifact_dir / f"{field}_pipeline.joblib"
            if not path.exists():
                raise FileNotFoundError(f"Missing sklearn artifact: {path}")
            self._pipelines[field] = joblib.load(path)

    def predict(self, text: str) -> dict:
        """Return {field: (label, confidence)} for a single ticket text."""
        result = {}
        for field, pipeline in self._pipelines.items():
            proba = pipeline.predict_proba([text])[0]
            classes = pipeline.classes_
            best_idx = proba.argmax()
            result[field] = (str(classes[best_idx]), float(proba[best_idx]))
        return result
