"""First-run bootstrap.

If the model registry is empty (fresh clone, empty DB), this trains the
lightweight sklearn baseline on the bundled example dataset and registers
+ auto-approves + activates it, so `POST /predict` works immediately with
no manual training step. Any later model (baseline or transformer) must go
through the normal approve/activate flow.
"""
from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.registry import model_registry
from app.training.evaluate import evaluate_model
from app.training.sklearn_baseline import SklearnBaselinePredictor
from app.training.train import train_baseline

logger = logging.getLogger("triageflow.bootstrap")


def ensure_bootstrap_model(db: Session) -> None:
    if model_registry.get_active(db) is not None:
        return

    logger.info("No active model found — bootstrapping default sklearn baseline from example dataset.")
    result = train_baseline()
    meta, split = result["meta"], result["split"]

    predictor = SklearnBaselinePredictor(meta["artifact_path"])
    report = evaluate_model(predictor, split.test)

    entry = model_registry.register_candidate(
        db,
        version=meta["version"],
        model_type="sklearn_baseline",
        artifact_path=meta["artifact_path"],
        metrics=report,
        dataset_start=meta.get("dataset_start"),
        dataset_end=meta.get("dataset_end"),
        dataset_version="bundled-example-dataset-v1",
        n_training_examples=meta.get("n_training_examples"),
        notes="Auto-bootstrapped on first run from bundled example dataset.",
    )
    model_registry.approve(db, entry.version, approver="system-bootstrap")
    model_registry.activate(db, entry.version)
    logger.info("Bootstrapped and activated model %s", entry.version)
