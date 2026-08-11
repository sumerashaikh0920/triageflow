"""Pydantic request/response models for the TriageFlow ML API."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# /predict
# ---------------------------------------------------------------------------
class TicketIn(BaseModel):
    ticket_id: Optional[str] = Field(
        default=None, description="Optional external ticket id from the main backend."
    )
    subject: str = Field(..., min_length=1, max_length=300)
    body: str = Field(..., min_length=1, max_length=20000)

    @field_validator("subject", "body")
    @classmethod
    def _strip(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("must not be blank")
        return v


class LabelConfidence(BaseModel):
    label: str
    confidence: float = Field(..., ge=0.0, le=1.0)


class PredictionOut(BaseModel):
    ticket_id: Optional[str] = None

    category: str
    subcategory: str
    urgency: str
    sentiment: str

    # Per-field confidences + an overall aggregate used for downstream gating.
    confidence: dict[str, float]
    overall_confidence: float

    routing_team: str
    reason: str

    model_version: str
    model_type: str  # "transformer" | "sklearn_baseline" | "heuristic_fallback"
    model_timestamp: datetime
    predicted_at: datetime
    latency_ms: float


# ---------------------------------------------------------------------------
# /health
# ---------------------------------------------------------------------------
class HealthOut(BaseModel):
    status: str
    service: str
    active_model_version: Optional[str] = None
    active_model_type: Optional[str] = None
    active_model_deployed_at: Optional[datetime] = None
    database_ok: bool


# ---------------------------------------------------------------------------
# Feedback
# ---------------------------------------------------------------------------
class FeedbackIn(BaseModel):
    ticket_id: str
    ticket_text: str

    original_category: str
    original_subcategory: str
    original_urgency: str
    original_sentiment: str
    original_confidence: float = Field(..., ge=0.0, le=1.0)
    model_version: str

    corrected_category: Optional[str] = None
    corrected_subcategory: Optional[str] = None
    corrected_urgency: Optional[str] = None
    corrected_sentiment: Optional[str] = None

    feedback_source: str = Field(
        default="agent", description="e.g. 'agent', 'qa_review', 'auto_audit'"
    )


class FeedbackReviewIn(BaseModel):
    review_status: str = Field(..., pattern="^(approved|rejected)$")
    reviewer: Optional[str] = None


class FeedbackOut(BaseModel):
    id: int
    ticket_id: str
    original_category: str
    corrected_category: Optional[str]
    original_urgency: str
    corrected_urgency: Optional[str]
    review_status: str
    feedback_source: str
    created_at: datetime

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Model registry
# ---------------------------------------------------------------------------
class ModelMetadataOut(BaseModel):
    version: str
    model_type: str
    dataset_start: Optional[datetime]
    dataset_end: Optional[datetime]
    trained_at: datetime
    metrics: dict
    approval_status: str
    deployment_status: str
    is_active: bool

    class Config:
        from_attributes = True


class RetrainRunOut(BaseModel):
    triggered: bool
    reason: str
    candidate_version: Optional[str] = None
    regressed: Optional[bool] = None
    report: Optional[dict] = None
