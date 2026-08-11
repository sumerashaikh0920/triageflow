"""Live inference predictor used by the FastAPI /predict endpoint.

Resolution order:
  1. Active model from the registry (transformer, if deployed; otherwise
     the sklearn baseline) — loaded lazily and cached in-process.
  2. If no active model, or loading/inference throws for any reason
     (corrupted artifact, missing optional dependency, etc.), fall back to
     the pure keyword heuristic so the API never 500s on a bad model state.
"""
from __future__ import annotations

import datetime as dt
import logging
import time
from dataclasses import dataclass
from typing import Optional

from app.db import session_scope
from app.inference.heuristic import classify as heuristic_classify
from app.inference.routing import routing_engine
from app.labels import SUBCATEGORY_TO_CATEGORY, default_subcategory_for
from app.registry import model_registry

logger = logging.getLogger("triageflow.predictor")


@dataclass
class LoadedModel:
    version: str
    model_type: str
    trained_at: dt.datetime
    predictor: object  # exposes .predict(text) -> {field: (label, confidence)}


class PredictorService:
    def __init__(self) -> None:
        self._cache: Optional[LoadedModel] = None
        self._cache_version: Optional[str] = None

    def _load_active_model(self) -> Optional[LoadedModel]:
        with session_scope() as db:
            active = model_registry.get_active(db)
            if active is None:
                return None
            version, model_type, artifact_path, trained_at = (
                active.version, active.model_type, active.artifact_path, active.trained_at,
            )

        try:
            if model_type == "sklearn_baseline":
                from app.training.sklearn_baseline import SklearnBaselinePredictor
                predictor = SklearnBaselinePredictor(artifact_path)
            elif model_type == "transformer":
                from app.inference.transformer_predictor import TransformerPredictorAdapter
                predictor = TransformerPredictorAdapter(artifact_path)
            else:
                logger.warning("Unknown model_type '%s' for active model %s", model_type, version)
                return None
        except Exception:
            logger.exception("Failed to load active model artifact for version %s", version)
            return None

        return LoadedModel(version=version, model_type=model_type, trained_at=trained_at, predictor=predictor)

    def get_model(self, force_reload: bool = False) -> Optional[LoadedModel]:
        if force_reload or self._cache is None:
            self._cache = self._load_active_model()
        return self._cache

    def invalidate_cache(self) -> None:
        self._cache = None

    def predict(self, subject: str, body: str, ticket_id: Optional[str] = None) -> dict:
        text = f"{subject}. {body}"
        start = time.perf_counter()

        loaded = self.get_model()
        used_fallback = False
        reason_prefix = ""

        if loaded is not None:
            try:
                raw = loaded.predictor.predict(text)
                category, cat_conf = raw["category"]
                subcategory, sub_conf = raw["subcategory"]
                urgency, urg_conf = raw["urgency"]
                sentiment, sent_conf = raw["sentiment"]

                # Guard against category/subcategory disagreement from
                # independently-predicted heads by preferring the
                # subcategory only if it's consistent with the predicted
                # category; otherwise fall back to a sane default so the
                # API never returns an internally-inconsistent pair.
                if SUBCATEGORY_TO_CATEGORY.get(subcategory) != category:
                    subcategory = default_subcategory_for(category)
                    sub_conf = min(sub_conf, cat_conf)

                confidence = {
                    "category": round(cat_conf, 4),
                    "subcategory": round(sub_conf, 4),
                    "urgency": round(urg_conf, 4),
                    "sentiment": round(sent_conf, 4),
                }
                model_version = loaded.version
                model_type = loaded.model_type
                model_timestamp = loaded.trained_at
                reason_prefix = (
                    f"Predicted by model '{model_version}' ({model_type}); "
                    f"category driven by strongest lexical/semantic signal, "
                    f"urgency by escalation language, sentiment by tone."
                )
            except Exception:
                logger.exception("Active model failed at inference time, falling back to heuristic.")
                used_fallback = True
        else:
            used_fallback = True

        if used_fallback:
            result = heuristic_classify(subject, body)
            category, subcategory = result.category, result.subcategory
            urgency, sentiment = result.urgency, result.sentiment
            confidence = result.confidence
            model_version = "heuristic-fallback-v1"
            model_type = "heuristic_fallback"
            model_timestamp = dt.datetime.utcnow()
            reason_prefix = result.reason

        routing_decision = routing_engine.route(category, urgency)
        overall_confidence = round(sum(confidence.values()) / len(confidence), 4)
        latency_ms = round((time.perf_counter() - start) * 1000, 3)

        reason = f"{reason_prefix} Routed to '{routing_decision.team}': {routing_decision.reason}"

        return {
            "ticket_id": ticket_id,
            "category": category,
            "subcategory": subcategory,
            "urgency": urgency,
            "sentiment": sentiment,
            "confidence": confidence,
            "overall_confidence": overall_confidence,
            "routing_team": routing_decision.team,
            "reason": reason,
            "model_version": model_version,
            "model_type": model_type,
            "model_timestamp": model_timestamp,
            "predicted_at": dt.datetime.utcnow(),
            "latency_ms": latency_ms,
        }


# Process-wide singleton (model artifacts are cached after first load).
predictor_service = PredictorService()
