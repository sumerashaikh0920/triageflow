"""Retraining trigger evaluation.

Two independent, configurable triggers — either one firing is enough to
recommend a retraining run:
  1. Weekly schedule: at least `retrain_weekly_interval_days` since the
     currently active model was trained.
  2. Minimum approved corrections: at least `retrain_min_approved_corrections`
     approved-but-not-yet-exported feedback rows have accumulated.

This module only *decides* whether a retrain should happen; running it is
`retrain.pipeline.RetrainPipeline.run()`. Kept separate so the decision
logic is trivially unit-testable without touching training code, and so it
can be called from either an APScheduler cron job or an on-demand API call.
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.config import settings
from app.feedback.ingest import count_approved_unexported
from app.registry import model_registry


@dataclass
class TriggerDecision:
    should_trigger: bool
    reasons: list[str]


def check_weekly_trigger(db: Session) -> tuple[bool, str]:
    if not settings.retrain_weekly_enabled:
        return False, "Weekly trigger disabled in config."

    active = model_registry.get_active(db)
    if active is None:
        return True, "No active model yet."

    age = dt.datetime.utcnow() - active.trained_at
    threshold = dt.timedelta(days=settings.retrain_weekly_interval_days)
    if age >= threshold:
        return True, f"Active model is {age.days} days old (threshold: {settings.retrain_weekly_interval_days})."
    return False, f"Active model is {age.days} days old (threshold not reached)."


def check_min_corrections_trigger(db: Session) -> tuple[bool, str]:
    n = count_approved_unexported(db)
    threshold = settings.retrain_min_approved_corrections
    if n >= threshold:
        return True, f"{n} approved corrections pending export (threshold: {threshold})."
    return False, f"Only {n} approved corrections pending export (threshold: {threshold})."


def evaluate_triggers(db: Session) -> TriggerDecision:
    weekly_fire, weekly_reason = check_weekly_trigger(db)
    count_fire, count_reason = check_min_corrections_trigger(db)

    reasons = [weekly_reason, count_reason]
    return TriggerDecision(should_trigger=weekly_fire or count_fire, reasons=reasons)
