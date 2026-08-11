"""
ORM tables owned by the ML service.

`ticket_feedback` — corrected labels supplied by support agents / QA
reviewers, used to build the human-feedback retraining loop.

`model_registry` — rollback-compatible registry of every trained model
(baseline sklearn or fine-tuned transformer), its metrics, and its
approval / deployment lifecycle state.
"""
from __future__ import annotations

import datetime as dt

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def _utcnow() -> dt.datetime:
    return dt.datetime.utcnow()


class TicketFeedback(Base):
    """A single agent/QA correction of a model prediction."""

    __tablename__ = "ticket_feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ticket_id: Mapped[str] = mapped_column(String(64), index=True)
    ticket_text: Mapped[str] = mapped_column(Text)

    # What the model predicted at the time.
    original_category: Mapped[str] = mapped_column(String(64))
    original_subcategory: Mapped[str] = mapped_column(String(64))
    original_urgency: Mapped[str] = mapped_column(String(32))
    original_sentiment: Mapped[str] = mapped_column(String(32))
    original_confidence: Mapped[float] = mapped_column(Float)
    model_version: Mapped[str] = mapped_column(String(64))

    # What a human said it should have been. Null means "prediction confirmed
    # correct" for that field.
    corrected_category: Mapped[str | None] = mapped_column(String(64), nullable=True)
    corrected_subcategory: Mapped[str | None] = mapped_column(String(64), nullable=True)
    corrected_urgency: Mapped[str | None] = mapped_column(String(32), nullable=True)
    corrected_sentiment: Mapped[str | None] = mapped_column(String(32), nullable=True)

    feedback_source: Mapped[str] = mapped_column(String(32), default="agent")

    # pending -> approved | rejected
    review_status: Mapped[str] = mapped_column(String(16), default="pending", index=True)
    reviewer: Mapped[str | None] = mapped_column(String(64), nullable=True)
    reviewed_at: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)

    # Set once this row has been pulled into a versioned training export,
    # so it isn't exported twice.
    exported_in_dataset_version: Mapped[str | None] = mapped_column(String(64), nullable=True)

    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_utcnow)

    def effective_label(self, field: str) -> str:
        """Return the corrected label if present, else the original prediction."""
        corrected = getattr(self, f"corrected_{field}")
        return corrected if corrected else getattr(self, f"original_{field}")

    def has_any_correction(self) -> bool:
        return any(
            [
                self.corrected_category,
                self.corrected_subcategory,
                self.corrected_urgency,
                self.corrected_sentiment,
            ]
        )


class ModelRegistryEntry(Base):
    """One row per trained model artifact (candidate or deployed)."""

    __tablename__ = "model_registry"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    version: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    model_type: Mapped[str] = mapped_column(String(32))  # sklearn_baseline | transformer
    artifact_path: Mapped[str] = mapped_column(String(512))

    dataset_start: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)
    dataset_end: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)
    dataset_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    n_training_examples: Mapped[int | None] = mapped_column(Integer, nullable=True)

    trained_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_utcnow)
    metrics: Mapped[dict] = mapped_column(JSON, default=dict)

    # pending -> approved | rejected
    approval_status: Mapped[str] = mapped_column(String(16), default="pending")
    # staged -> active -> retired  (rolled_back is used when reactivated via rollback)
    deployment_status: Mapped[str] = mapped_column(String(16), default="staged")
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)

    # If this candidate was compared against a previous model and regressed,
    # we keep the record but it can never be auto-deployed.
    regressed_vs_active: Mapped[bool] = mapped_column(Boolean, default=False)
    compared_against_version: Mapped[str | None] = mapped_column(String(64), nullable=True)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_utcnow)
