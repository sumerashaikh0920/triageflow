"""End-to-end retraining pipeline.

Stages (matches the spec exactly):
  1. validate_labels   — app.feedback.export.validate_approved_feedback
  2. snapshot_dataset   — app.feedback.export.export_approved_feedback
  3. train               — app.training.train.{train_baseline,train_transformer}
  4. evaluate             — app.training.evaluate.evaluate_model
  5. compare_against_current — app.registry.model_registry.compare_metrics
  6. register_candidate    — app.registry.model_registry.register_candidate
  7. require_approval       — candidate stays approval_status='pending';
                               a human (or CI gate) must call approve()
  8. deploy/activate        — separate, explicit call to activate();
                               NEVER performed automatically by this pipeline.

The one hard safety rule enforced at *two* layers (pipeline AND registry):
a candidate whose primary metric regresses vs. the active model beyond
`retrain_regression_tolerance` is marked `regressed_vs_active=True` and can
never be approved or activated, even by mistake.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from app.config import settings
from app.feedback.export import export_approved_feedback, validate_approved_feedback
from app.registry import model_registry
from app.training.evaluate import evaluate_model
from app.training.sklearn_baseline import SklearnBaselinePredictor
from app.training.train import train_baseline, train_transformer

logger = logging.getLogger("triageflow.retrain")


@dataclass
class RetrainReport:
    triggered: bool
    reason: str
    dataset_manifest: Optional[dict] = None
    candidate_version: Optional[str] = None
    candidate_metrics: Optional[dict] = None
    active_version: Optional[str] = None
    active_metrics: Optional[dict] = None
    regressed: Optional[bool] = None
    stage_reached: str = "not_started"
    problems: list[str] = field(default_factory=list)


class RetrainPipeline:
    def __init__(self, mode: str = "baseline"):
        """`mode` selects which trainer to run: 'baseline' (fast, default)
        or 'transformer' (fine-tune, heavier)."""
        if mode not in ("baseline", "transformer"):
            raise ValueError("mode must be 'baseline' or 'transformer'")
        self.mode = mode

    def run(self, db: Session, force: bool = False) -> RetrainReport:
        report = RetrainReport(triggered=False, reason="")

        # --- Stage 1: validate labels ---
        report.stage_reached = "validate_labels"
        valid_rows, problems = validate_approved_feedback(db)
        report.problems = problems
        if not valid_rows and not force:
            report.reason = "No valid approved corrections available to retrain on."
            return report

        # --- Stage 2: snapshot dataset ---
        report.stage_reached = "snapshot_dataset"
        manifest = export_approved_feedback(db)
        report.dataset_manifest = manifest
        dataset_path = Path(manifest["dataset_path"]) if manifest.get("dataset_path") else None

        if dataset_path is None and not force:
            report.reason = "No dataset snapshot produced (nothing new to export) and force=False."
            return report
        if dataset_path is None:
            dataset_path = settings.example_dataset_path  # force-retrain on base data only

        # --- Stage 3: train ---
        report.stage_reached = "train"
        try:
            if self.mode == "baseline":
                result = train_baseline(dataset_path=dataset_path)
            else:
                result = train_transformer(dataset_path=dataset_path)
        except Exception as exc:
            logger.exception("Training failed during retraining pipeline")
            report.reason = f"Training failed: {exc}"
            return report

        meta, split = result["meta"], result["split"]

        # --- Stage 4: evaluate ---
        report.stage_reached = "evaluate"
        if meta["model_type"] == "sklearn_baseline":
            candidate_predictor = SklearnBaselinePredictor(meta["artifact_path"])
        else:
            from app.inference.transformer_predictor import TransformerPredictorAdapter
            candidate_predictor = TransformerPredictorAdapter(meta["artifact_path"])

        candidate_metrics = evaluate_model(candidate_predictor, split.test)
        report.candidate_metrics = candidate_metrics

        # --- Stage 5: compare against current active model ---
        report.stage_reached = "compare_against_current"
        active_entry = model_registry.get_active(db)
        active_metrics = active_entry.metrics if active_entry else None
        report.active_version = active_entry.version if active_entry else None
        report.active_metrics = active_metrics

        regressed = model_registry.compare_metrics(
            candidate_metrics, active_metrics, settings.retrain_regression_tolerance
        )
        report.regressed = regressed

        # --- Stage 6: register candidate (always registered, win or lose,
        #     for full audit trail — but regressed models are locked out of
        #     approval/activation at the registry layer). ---
        report.stage_reached = "register_candidate"
        entry = model_registry.register_candidate(
            db,
            version=meta["version"],
            model_type=meta["model_type"],
            artifact_path=meta["artifact_path"],
            metrics=candidate_metrics,
            dataset_start=manifest.get("dataset_start"),
            dataset_end=manifest.get("dataset_end"),
            dataset_version=manifest.get("dataset_version"),
            n_training_examples=meta.get("n_training_examples"),
            regressed_vs_active=regressed,
            compared_against_version=report.active_version,
            notes="Produced by automated retraining pipeline."
            + (" REGRESSED vs active model — blocked from deployment." if regressed else ""),
        )
        report.candidate_version = entry.version

        # --- Stage 7: require approval (no-op here — approval is a
        #     separate, explicit action via the API/registry) ---
        report.stage_reached = "awaiting_approval" if not regressed else "blocked_regressed"

        report.triggered = True
        report.reason = (
            "Regression detected — candidate registered but requires manual review; "
            "automatic deployment blocked."
            if regressed
            else "Candidate trained, evaluated, and registered. Awaiting human approval before deployment."
        )
        return report
