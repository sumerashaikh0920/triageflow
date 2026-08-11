from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator

from app.core.constants import UrgencyEnum


class FeedbackBase(BaseModel):
    ticket_id: str
    user_id: Optional[str] = None  # falls back to the authenticated user if omitted
    prediction_id: Optional[str] = None
    notes: Optional[str] = None


class CorrectCategoryRequest(FeedbackBase):
    original_category: Optional[str] = None
    corrected_category: str


class MarkUrgencyRequest(FeedbackBase):
    original_urgency: Optional[UrgencyEnum] = None
    corrected_urgency: UrgencyEnum


class AcceptPredictionRequest(FeedbackBase):
    pass


class FeedbackRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    ticket_id: str
    prediction_id: Optional[str] = None
    user_id: str
    original_category: Optional[str] = None
    corrected_category: Optional[str] = None
    original_urgency: Optional[UrgencyEnum] = None
    corrected_urgency: Optional[UrgencyEnum] = None
    accepted: bool
    notes: Optional[str] = None
    created_at: datetime
