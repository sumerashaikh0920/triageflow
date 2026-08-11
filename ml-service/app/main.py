"""TriageFlow ML service — FastAPI app.

Endpoints:
  POST /predict                     — classify a ticket, get routing + explanation
  GET  /health                      — liveness/readiness + active model info

  POST /feedback                    — record an agent/QA correction
  GET  /feedback                    — list feedback (filter by review_status)
  POST /feedback/{id}/review        — approve/reject a feedback row

  GET  /models                      — list registry entries
  GET  /models/active                — current active model metadata
  POST /models/{version}/approve     — approve a candidate
  POST /models/{version}/activate    — deploy an approved, non-regressed model
  POST /models/{version}/rollback    — reactivate a previously retired model

  POST /retrain/check                — evaluate triggers without running training
  POST /retrain/run                  — run the retraining pipeline (registers a candidate;
                                        never auto-deploys)

This service is designed to sit alongside the main FastAPI/PostgreSQL
backend as an independent deployable — see README.md for integration
patterns (sync HTTP call vs. queue-based).
"""
from __future__ import annotations

import datetime as dt
import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.db import check_connection, get_db, init_db, session_scope
from app.feedback import ingest as feedback_ingest
from app.inference.predictor import predictor_service
from app.registry import model_registry
from app.registry.bootstrap import ensure_bootstrap_model
from app.retrain.pipeline import RetrainPipeline
from app.retrain.scheduler import evaluate_triggers
from app.schemas import (
    FeedbackIn,
    FeedbackOut,
    FeedbackReviewIn,
    HealthOut,
    ModelMetadataOut,
    PredictionOut,
    RetrainRunOut,
    TicketIn,
)
from app.utils.logging import configure_logging

logger = logging.getLogger("triageflow.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    logger.info("Starting %s (env=%s)", settings.service_name, settings.ml_service_env)
    init_db()
    with session_scope() as db:
        ensure_bootstrap_model(db)
    predictor_service.invalidate_cache()

    scheduler = _maybe_start_scheduler()
    yield
    if scheduler is not None:
        scheduler.shutdown(wait=False)


def _maybe_start_scheduler():
    """Optional background job that checks (but does not act on) weekly /
    correction-count retraining triggers once a day, logging a clear signal
    an operator can wire up to an alert. Disabled automatically under pytest."""
    if not settings.retrain_weekly_enabled:
        return None
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
    except ImportError:
        logger.warning("APScheduler not installed; skipping background trigger checks.")
        return None

    def _job():
        with session_scope() as db:
            decision = evaluate_triggers(db)
            if decision.should_trigger:
                logger.info("Retrain trigger conditions met: %s", decision.reasons)
            else:
                logger.debug("Retrain trigger check: no trigger. %s", decision.reasons)

    scheduler = BackgroundScheduler()
    scheduler.add_job(_job, "interval", hours=24, id="retrain_trigger_check")
    scheduler.start()
    return scheduler


app = FastAPI(
    title="TriageFlow ML Service",
    description="Ticket classification, routing, and human-feedback-driven retraining for TriageFlow.",
    version="1.0.0",
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# Core inference
# ---------------------------------------------------------------------------
@app.post("/predict", response_model=PredictionOut)
def predict(ticket: TicketIn) -> PredictionOut:
    result = predictor_service.predict(ticket.subject, ticket.body, ticket.ticket_id)
    return PredictionOut(**result)


@app.get("/health", response_model=HealthOut)
def health(db: Session = Depends(get_db)) -> HealthOut:
    db_ok = check_connection()
    active = model_registry.get_active(db) if db_ok else None
    return HealthOut(
        status="ok" if db_ok else "degraded",
        service=settings.service_name,
        active_model_version=active.version if active else None,
        active_model_type=active.model_type if active else None,
        active_model_deployed_at=active.trained_at if active else None,
        database_ok=db_ok,
    )


# ---------------------------------------------------------------------------
# Feedback loop
# ---------------------------------------------------------------------------
@app.post("/feedback", response_model=FeedbackOut, status_code=201)
def submit_feedback(feedback: FeedbackIn, db: Session = Depends(get_db)) -> FeedbackOut:
    row = feedback_ingest.record_feedback(db, **feedback.model_dump())
    return FeedbackOut.model_validate(row)


@app.get("/feedback", response_model=list[FeedbackOut])
def get_feedback(review_status: str | None = None, db: Session = Depends(get_db)) -> list[FeedbackOut]:
    rows = feedback_ingest.list_feedback(db, review_status=review_status)
    return [FeedbackOut.model_validate(r) for r in rows]


@app.post("/feedback/{feedback_id}/review", response_model=FeedbackOut)
def review_feedback(feedback_id: int, review: FeedbackReviewIn, db: Session = Depends(get_db)) -> FeedbackOut:
    try:
        row = feedback_ingest.review_feedback(db, feedback_id, review.review_status, review.reviewer)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return FeedbackOut.model_validate(row)


# ---------------------------------------------------------------------------
# Model registry
# ---------------------------------------------------------------------------
@app.get("/models", response_model=list[ModelMetadataOut])
def list_models(db: Session = Depends(get_db)) -> list[ModelMetadataOut]:
    return [ModelMetadataOut.model_validate(m) for m in model_registry.list_models(db)]


@app.get("/models/active", response_model=ModelMetadataOut)
def get_active_model(db: Session = Depends(get_db)) -> ModelMetadataOut:
    active = model_registry.get_active(db)
    if active is None:
        raise HTTPException(status_code=404, detail="No active model.")
    return ModelMetadataOut.model_validate(active)


@app.post("/models/{version}/approve", response_model=ModelMetadataOut)
def approve_model(version: str, approver: str | None = None, db: Session = Depends(get_db)) -> ModelMetadataOut:
    try:
        entry = model_registry.approve(db, version, approver)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:  # RegressedModelDeploymentError
        raise HTTPException(status_code=409, detail=str(exc))
    return ModelMetadataOut.model_validate(entry)


@app.post("/models/{version}/activate", response_model=ModelMetadataOut)
def activate_model(version: str, db: Session = Depends(get_db)) -> ModelMetadataOut:
    try:
        entry = model_registry.activate(db, version)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    predictor_service.invalidate_cache()
    return ModelMetadataOut.model_validate(entry)


@app.post("/models/{version}/rollback", response_model=ModelMetadataOut)
def rollback_model(version: str, db: Session = Depends(get_db)) -> ModelMetadataOut:
    try:
        entry = model_registry.rollback(db, version)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    predictor_service.invalidate_cache()
    return ModelMetadataOut.model_validate(entry)


# ---------------------------------------------------------------------------
# Retraining
# ---------------------------------------------------------------------------
@app.post("/retrain/check", response_model=RetrainRunOut)
def check_retrain(db: Session = Depends(get_db)) -> RetrainRunOut:
    decision = evaluate_triggers(db)
    return RetrainRunOut(
        triggered=decision.should_trigger,
        reason="; ".join(decision.reasons),
    )


@app.post("/retrain/run", response_model=RetrainRunOut)
def run_retrain(mode: str = "baseline", force: bool = False, db: Session = Depends(get_db)) -> RetrainRunOut:
    pipeline = RetrainPipeline(mode=mode)
    report = pipeline.run(db, force=force)
    return RetrainRunOut(
        triggered=report.triggered,
        reason=report.reason,
        candidate_version=report.candidate_version,
        regressed=report.regressed,
        report={
            "stage_reached": report.stage_reached,
            "dataset_manifest": report.dataset_manifest,
            "candidate_metrics": report.candidate_metrics,
            "active_version": report.active_version,
            "problems": report.problems,
        },
    )
