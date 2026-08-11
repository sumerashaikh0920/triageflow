"""Ingest and query human feedback (agent/QA corrections of predictions).

This module is the write/read layer the main FastAPI backend (or an agent
UI) talks to when a support agent corrects a ticket's predicted labels.
"""
from __future__ import annotations

import datetime as dt
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models_db import TicketFeedback


def record_feedback(
    db: Session,
    *,
    ticket_id: str,
    ticket_text: str,
    original_category: str,
    original_subcategory: str,
    original_urgency: str,
    original_sentiment: str,
    original_confidence: float,
    model_version: str,
    corrected_category: Optional[str] = None,
    corrected_subcategory: Optional[str] = None,
    corrected_urgency: Optional[str] = None,
    corrected_sentiment: Optional[str] = None,
    feedback_source: str = "agent",
) -> TicketFeedback:
    row = TicketFeedback(
        ticket_id=ticket_id,
        ticket_text=ticket_text,
        original_category=original_category,
        original_subcategory=original_subcategory,
        original_urgency=original_urgency,
        original_sentiment=original_sentiment,
        original_confidence=original_confidence,
        model_version=model_version,
        corrected_category=corrected_category,
        corrected_subcategory=corrected_subcategory,
        corrected_urgency=corrected_urgency,
        corrected_sentiment=corrected_sentiment,
        feedback_source=feedback_source,
        review_status="pending",
        created_at=dt.datetime.utcnow(),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def review_feedback(
    db: Session, feedback_id: int, review_status: str, reviewer: Optional[str] = None
) -> TicketFeedback:
    if review_status not in ("approved", "rejected"):
        raise ValueError("review_status must be 'approved' or 'rejected'")
    row = db.get(TicketFeedback, feedback_id)
    if row is None:
        raise ValueError(f"No feedback row with id={feedback_id}")
    row.review_status = review_status
    row.reviewer = reviewer
    row.reviewed_at = dt.datetime.utcnow()
    db.commit()
    db.refresh(row)
    return row


def list_feedback(
    db: Session, review_status: Optional[str] = None, limit: int = 100
) -> list[TicketFeedback]:
    stmt = select(TicketFeedback).order_by(TicketFeedback.created_at.desc()).limit(limit)
    if review_status:
        stmt = stmt.where(TicketFeedback.review_status == review_status)
    return list(db.execute(stmt).scalars())


def count_approved_unexported(db: Session) -> int:
    """Number of approved corrections not yet pulled into a training export
    — this is what the count-based retraining trigger checks."""
    stmt = select(func.count()).select_from(TicketFeedback).where(
        TicketFeedback.review_status == "approved",
        TicketFeedback.exported_in_dataset_version.is_(None),
    )
    return db.execute(stmt).scalar_one()
